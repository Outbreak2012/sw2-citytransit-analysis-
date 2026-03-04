import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.ml.bert_model import BERTSentimentAnalyzer, HAS_TRANSFORMERS


client = TestClient(app)


def get_auth_header():
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_analyze_sentiment():
    payload = {"text": "Me encanta este servicio"}
    resp = client.post("/api/v1/analytics/sentiment/analyze", json=payload, headers=get_auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert "sentiment" in data


# ==================== UNIT TESTS FOR BERT ====================

@pytest.fixture
def bert_analyzer():
    """Create a fresh BERT analyzer for each test"""
    return BERTSentimentAnalyzer()


class TestBERTAnalysis:
    """Tests for BERT sentiment analysis"""
    
    def test_analyze_positive_text(self, bert_analyzer):
        """Test analyzing positive sentiment text"""
        result = bert_analyzer.analyze("Excelente servicio, muy recomendado")
        
        assert 'sentiment' in result
        assert 'confidence_score' in result
        assert 'scores' in result
        assert result['sentiment'] in ['POSITIVE', 'NEUTRAL', 'NEGATIVE']
    
    def test_analyze_negative_text(self, bert_analyzer):
        """Test analyzing negative sentiment text"""
        result = bert_analyzer.analyze("Pésimo servicio, nunca vuelvo")
        
        assert result['sentiment'] == 'NEGATIVE'
    
    def test_analyze_neutral_text(self, bert_analyzer):
        """Test analyzing neutral sentiment text"""
        result = bert_analyzer.analyze("El servicio estuvo normal")
        
        assert result['sentiment'] in ['NEUTRAL', 'POSITIVE']
    
    def test_analyze_empty_text(self, bert_analyzer):
        """Test analyzing empty text returns neutral"""
        result = bert_analyzer.analyze("")
        
        assert result['sentiment'] == 'NEUTRAL'
        assert result['method'] == 'empty'
    
    def test_analyze_with_tracking(self, bert_analyzer):
        """Test that analyze_with_tracking updates counters"""
        initial_count = bert_analyzer.total_analyzed
        
        bert_analyzer.analyze_with_tracking("Texto de prueba")
        
        assert bert_analyzer.total_analyzed == initial_count + 1
        assert len(bert_analyzer.analysis_history) > 0


class TestBERTBatchAnalysis:
    """Tests for BERT batch analysis"""
    
    def test_batch_analyze_multiple_texts(self, bert_analyzer):
        """Test batch analyzing multiple texts"""
        texts = [
            "Excelente servicio",
            "Muy malo",
            "Normal"
        ]
        
        results = bert_analyzer.batch_analyze(texts)
        
        assert len(results) == 3
        assert all('sentiment' in r for r in results)
    
    def test_batch_analyze_empty_list(self, bert_analyzer):
        """Test batch analyzing empty list"""
        results = bert_analyzer.batch_analyze([])
        
        assert results == []


class TestBERTSummaryStats:
    """Tests for BERT summary statistics"""
    
    def test_get_summary_stats(self, bert_analyzer):
        """Test getting summary statistics"""
        sentiments = [
            {'sentiment': 'POSITIVE', 'confidence_score': 0.8, 'method': 'rules'},
            {'sentiment': 'NEGATIVE', 'confidence_score': 0.7, 'method': 'rules'},
            {'sentiment': 'NEUTRAL', 'confidence_score': 0.6, 'method': 'rules'},
        ]
        
        stats = bert_analyzer.get_summary_stats(sentiments)
        
        assert stats['total'] == 3
        assert stats['positive'] == 1
        assert stats['negative'] == 1
        assert stats['neutral'] == 1
        assert 'avg_confidence' in stats
    
    def test_get_summary_stats_empty(self, bert_analyzer):
        """Test getting summary stats with empty list"""
        stats = bert_analyzer.get_summary_stats([])
        
        assert stats['total'] == 0


class TestBERTTrainingData:
    """Tests for BERT training data generation"""
    
    def test_generate_training_data_balanced(self, bert_analyzer):
        """Test generating balanced training data"""
        data = bert_analyzer.generate_training_data(num_samples=30, balanced=True)
        
        assert len(data) >= 27  # 3 * 9 (integer division)
        assert all('text' in item and 'label' in item for item in data)
        
        labels = [item['label'] for item in data]
        assert 'POSITIVE' in labels
        assert 'NEGATIVE' in labels
        assert 'NEUTRAL' in labels
    
    def test_generate_training_data_unbalanced(self, bert_analyzer):
        """Test generating unbalanced (realistic) training data"""
        data = bert_analyzer.generate_training_data(num_samples=100, balanced=False)
        
        labels = [item['label'] for item in data]
        neutral_count = labels.count('NEUTRAL')
        
        # Neutral should be the majority
        assert neutral_count > len(data) * 0.5


class TestBERTEvaluation:
    """Tests for BERT model evaluation"""
    
    def test_evaluate_accuracy(self, bert_analyzer):
        """Test evaluating model accuracy"""
        test_data = [
            {'text': 'Excelente servicio', 'label': 'POSITIVE'},
            {'text': 'Pésimo servicio', 'label': 'NEGATIVE'},
            {'text': 'Normal', 'label': 'NEUTRAL'},
        ]
        
        result = bert_analyzer.evaluate_accuracy(test_data)
        
        assert 'accuracy' in result
        assert 'total_samples' in result
        assert 'confusion_matrix' in result
        assert 'metrics_per_class' in result
    
    def test_evaluate_accuracy_empty(self, bert_analyzer):
        """Test evaluating with empty data"""
        result = bert_analyzer.evaluate_accuracy([])
        
        assert 'error' in result


class TestBERTPersistence:
    """Tests for BERT config save/load"""
    
    def test_save_config(self, bert_analyzer):
        """Test saving configuration"""
        bert_analyzer.total_analyzed = 100
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bert_config.json")
            saved_path = bert_analyzer.save_config(path)
            
            assert os.path.exists(saved_path)
    
    def test_load_config(self, bert_analyzer):
        """Test loading configuration"""
        bert_analyzer.total_analyzed = 50
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bert_config.json")
            bert_analyzer.save_config(path)
            
            # Create new analyzer and load
            new_analyzer = BERTSentimentAnalyzer()
            new_analyzer.config_path = path
            success = new_analyzer.load_config(path)
            
            assert success
            assert new_analyzer.total_analyzed == 50
    
    def test_load_nonexistent_config(self, bert_analyzer):
        """Test loading nonexistent config returns False"""
        result = bert_analyzer.load_config("/nonexistent/path/config.json")
        assert result is False


class TestBERTModelInfo:
    """Tests for BERT model info"""
    
    def test_get_model_info(self, bert_analyzer):
        """Test getting model info"""
        info = bert_analyzer.get_model_info()
        
        assert 'is_loaded' in info
        assert 'has_transformers' in info
        assert 'available_models' in info
        assert 'total_analyzed' in info
    
    def test_get_analysis_stats(self, bert_analyzer):
        """Test getting analysis stats"""
        # Analyze some texts first
        bert_analyzer.analyze_with_tracking("Texto positivo")
        bert_analyzer.analyze_with_tracking("Texto negativo")
        
        stats = bert_analyzer.get_analysis_stats()
        
        assert stats['total_analyzed'] >= 2
        assert 'sentiment_distribution' in stats
        assert 'method_distribution' in stats


class TestBERTRuleBased:
    """Tests for rule-based analysis"""
    
    def test_rule_based_bolivian_expressions(self, bert_analyzer):
        """Test rule-based analysis with Bolivian expressions"""
        result = bert_analyzer._rule_based_analyze("Chévere el servicio, está yesca")
        
        assert result['sentiment'] == 'POSITIVE'
        assert result['method'] == 'rules'
    
    def test_rule_based_with_negator(self, bert_analyzer):
        """Test rule-based analysis handles negators"""
        result = bert_analyzer._rule_based_analyze("No es bueno el servicio")
        
        # With negator, positive becomes negative
        assert result['sentiment'] in ['NEGATIVE', 'NEUTRAL']
    
    def test_rule_based_with_intensifier(self, bert_analyzer):
        """Test rule-based analysis handles intensifiers"""
        result = bert_analyzer._rule_based_analyze("Muy malo el servicio")
        
        assert result['sentiment'] == 'NEGATIVE'
        assert result['confidence_score'] > 0.6
