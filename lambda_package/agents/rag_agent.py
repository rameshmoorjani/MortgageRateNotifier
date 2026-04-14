"""
RAG Agent - Generates trustworthy explanations with citations.

Features:
- Retrieves relevant financial documents
- Generates explanations with citations
- Provides confidence scoring
- Tracks source attribution
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from agents.knowledge_base import KnowledgeBase, Document


@dataclass
class Citation:
    """A citation for a recommendation."""
    document_id: str
    title: str
    source: str
    relevance_score: float
    quote: str  # Relevant excerpt


@dataclass
class ExplanationWithCitations:
    """An explanation with supporting citations."""
    explanation: str
    citations: List[Citation]
    confidence_score: float  # 0.0-1.0
    reasoning: str
    timestamp: str


class RAGAgent:
    """
    Retrieval-Augmented Generation Agent for trustworthy recommendations.
    """
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        """
        Initialize RAG agent.
        
        Args:
            knowledge_base: Knowledge base instance (creates default if None)
        """
        self.logger = logging.getLogger("RAGAgent")
        
        if knowledge_base is None:
            from agents.knowledge_base import create_default_knowledge_base
            self.kb = create_default_knowledge_base()
        else:
            self.kb = knowledge_base
    
    def explain_prediction(self, 
                          prediction: Dict,
                          user_data: Dict) -> ExplanationWithCitations:
        """
        Generate explanation for rate prediction with citations.
        
        Args:
            prediction: Prediction result from ML model
            user_data: User mortgage data
            
        Returns:
            Explanation with citations
        """
        direction = prediction.get('predicted_direction', 'STABLE')
        confidence = prediction.get('reliability', {}).get('overall_reliability', 0.5)
        
        # Build query for knowledge base
        query = f"Mortgage rates {direction.lower()} refinancing decision"
        
        # Retrieve relevant documents
        results = self.kb.retrieve(query, top_k=3)
        
        # Generate explanation
        explanation = self._generate_rate_explanation(direction, confidence, prediction)
        
        # Create citations
        citations = [
            Citation(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                relevance_score=score,
                quote=self._extract_quote(doc, direction)
            )
            for doc, score in zip(results.documents, results.scores)
        ]
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(confidence, results.scores)
        
        reasoning = f"Prediction based on {len(citations)} financial sources"
        
        return ExplanationWithCitations(
            explanation=explanation,
            citations=citations,
            confidence_score=confidence_score,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
    
    def explain_decision(self, 
                        decision: Dict,
                        financial_analysis: Dict,
                        user_data: Dict) -> ExplanationWithCitations:
        """
        Generate explanation for refinancing decision with citations.
        
        Args:
            decision: Decision result
            financial_analysis: Financial analysis
            user_data: User data
            
        Returns:
            Explanation with citations
        """
        decision_type = decision.get('decision', 'MONITOR')
        breakeven = financial_analysis.get('breakeven_months', 0)
        safety = financial_analysis.get('is_financially_safe', False)
        
        # Build query for knowledge base
        query = f"Refinancing {decision_type.lower()} break-even financial safety"
        
        # Retrieve relevant documents
        results = self.kb.retrieve(query, top_k=3)
        
        # Generate explanation
        explanation = self._generate_decision_explanation(
            decision_type, breakeven, safety, financial_analysis
        )
        
        # Create citations
        citations = [
            Citation(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                relevance_score=score,
                quote=self._extract_decision_quote(doc, decision_type, breakeven)
            )
            for doc, score in zip(results.documents, results.scores)
        ]
        
        # Calculate confidence score based on financial metrics
        confidence_score = self._calculate_financial_confidence(safety, breakeven)
        
        reasoning = f"Decision based on {len(citations)} financial sources and break-even analysis"
        
        return ExplanationWithCitations(
            explanation=explanation,
            citations=citations,
            confidence_score=confidence_score,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_rate_explanation(self, direction: str, confidence: float, 
                                   prediction: Dict) -> str:
        """Generate explanation for rate prediction."""
        avg_rate = prediction.get('predicted_average_30d', 0)
        current_rate = prediction.get('current_rate', 0)
        change = current_rate - avg_rate
        
        if direction == "DOWN":
            return (
                f"Based on current market analysis and forecasting models, mortgage rates are predicted "
                f"to trend downward over the next 30 days. Current rates are around {current_rate:.2f}%, "
                f"with average predicted rates of {avg_rate:.2f}% (a potential {abs(change):.2f}% decrease). "
                f"This prediction has {confidence*100:.0f}% confidence level. For homeowners with rates above "
                f"the market average, this trend presents a refinancing opportunity."
            )
        elif direction == "UP":
            return (
                f"Based on current market analysis and forecasting models, mortgage rates are predicted "
                f"to trend upward over the next 30 days. Current rates are around {current_rate:.2f}%, "
                f"with average predicted rates of {avg_rate:.2f}% (a potential {change:.2f}% increase). "
                f"This prediction has {confidence*100:.0f}% confidence level. If refinancing is being considered, "
                f"waiting could result in higher costs."
            )
        else:
            return (
                f"Based on current market analysis, mortgage rates are predicted to remain relatively stable "
                f"around {avg_rate:.2f}%. Current rates are {current_rate:.2f}%. With {confidence*100:.0f}% confidence, "
                f"the market shows little near-term movement, suggesting moderate urgency for refinancing decisions."
            )
    
    def _generate_decision_explanation(self, decision: str, breakeven: int, 
                                       safety: bool, analysis: Dict) -> str:
        """Generate explanation for refinancing decision."""
        monthly_savings = analysis.get('potential_monthly_saving', 0)
        remaining_months = analysis.get('remaining_loan_term_months', 0)
        credit_score = analysis.get('credit_score', 700)
        
        if decision == "REFINANCE NOW":
            return (
                f"RECOMMENDATION: Refinance your mortgage now. Analysis shows you could save ${monthly_savings:.0f}/month "
                f"with an estimated break-even point of {breakeven} months. With a remaining loan term of {remaining_months} months, "
                f"your mortgage will be paid off {remaining_months - breakeven} months after break-even, ensuring positive financial benefit. "
                f"Your credit score of {credit_score} means you qualify for favorable refinancing rates. Act soon as rate windows can close quickly."
            )
        elif decision == "REFINANCE IMMEDIATELY":
            return (
                f"RECOMMENDATION: Refinance your mortgage immediately. Rates are rising and refinancing now will lock in current rates. "
                f"You stand to save ${monthly_savings:.0f}/month with a rapid {breakeven}-month break-even. "
                f"Delaying could result in missing this refinancing window as rates increase."
            )
        elif decision == "WAIT 1-2 WEEKS":
            return (
                f"RECOMMENDATION: Wait 1-2 weeks before refinancing. While rates are trending in your favor, "
                f"the predicted decline suggests better opportunities in the near term. With potential savings of ${monthly_savings:.0f}/month "
                f"and a {breakeven}-month break-even, the math supports refinancing, but patience could improve terms. "
                f"Monitor the market and refinance if rates don't continue declining."
            )
        elif decision == "MONITOR":
            return (
                f"RECOMMENDATION: Monitor the market. Current conditions don't show a compelling refinancing opportunity. "
                f"With projected break-even of {breakeven} months and potential monthly savings of ${monthly_savings:.0f}, "
                f"the numbers are marginal. Track rate movements over the next 4 weeks and revisit if rates decline."
            )
        else:
            return (
                f"RECOMMENDATION: Do not refinance at this time. Your current mortgage terms are favorable compared to market rates. "
                f"If rates decline significantly (0.5%+ below your current rate), revisit this analysis."
            )
    
    def _extract_quote(self, doc: Document, direction: str) -> str:
        """Extract relevant quote from document."""
        content_lower = doc.content.lower()
        direction_lower = direction.lower()
        
        # Find sentences mentioning the rate direction
        sentences = doc.content.split('.')
        for sentence in sentences:
            if direction_lower in sentence.lower():
                return sentence.strip()[:150]
        
        # Fallback to first relevant sentence
        for sentence in sentences:
            if 'rate' in sentence.lower() or 'refinance' in sentence.lower():
                return sentence.strip()[:150]
        
        return doc.content[:150]
    
    def _extract_decision_quote(self, doc: Document, decision: str, breakeven: int) -> str:
        """Extract relevant quote for decision."""
        sentences = doc.content.split('.')
        
        # Look for break-even related content
        for sentence in sentences:
            if 'break-even' in sentence.lower() or 'months' in sentence.lower():
                return sentence.strip()[:150]
        
        # Look for decision-related content
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['safe', 'cost', 'benefit', 'decision']):
                return sentence.strip()[:150]
        
        return doc.content[:150]
    
    def _calculate_confidence(self, prediction_confidence: float, 
                             document_scores: List[float]) -> float:
        """
        Calculate overall confidence score.
        
        Args:
            prediction_confidence: ML model confidence
            document_scores: Relevance scores from knowledge base
            
        Returns:
            Overall confidence 0.0-1.0
        """
        # Combine prediction confidence with document support
        doc_support = sum(document_scores) / len(document_scores) if document_scores else 0.5
        
        # Weighted average: 60% model, 40% document support
        combined = (prediction_confidence * 0.6) + (doc_support * 0.4)
        
        return min(1.0, max(0.0, combined))
    
    def _calculate_financial_confidence(self, safety: bool, breakeven: int) -> float:
        """
        Calculate confidence based on financial metrics.
        
        Args:
            safety: Is financially safe
            breakeven: Break-even months
            
        Returns:
            Confidence 0.0-1.0
        """
        confidence = 0.5
        
        # Higher confidence if financially safe
        if safety:
            confidence += 0.2
        
        # Higher confidence if break-even is reasonable
        if breakeven < 12:
            confidence += 0.2
        elif breakeven < 24:
            confidence += 0.1
        # Reduce confidence if break-even is long (< 12 months increases, < 24 increases less)
        
        return min(1.0, max(0.0, confidence))
    
    def get_sources_summary(self, explanation: ExplanationWithCitations) -> str:
        """Get formatted summary of sources."""
        summary = "**Sources:**\n"
        for i, citation in enumerate(explanation.citations, 1):
            summary += f"{i}. {citation.title} - {citation.source} ({citation.relevance_score:.0%} relevant)\n"
        return summary


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    agent = RAGAgent()
    
    # Sample prediction
    sample_prediction = {
        'predicted_direction': 'DOWN',
        'predicted_average_30d': 4.0,
        'current_rate': 4.5,
        'reliability': {'overall_reliability': 0.82}
    }
    
    sample_user = {'credit_score': 750}
    
    # Generate explanation with citations
    explanation = agent.explain_prediction(sample_prediction, sample_user)
    
    print("="*70)
    print("RATE PREDICTION EXPLANATION")
    print("="*70)
    print(explanation.explanation)
    print(f"\nConfidence: {explanation.confidence_score*100:.0f}%")
    print(f"Reasoning: {explanation.reasoning}")
    print("\n" + agent.get_sources_summary(explanation))
