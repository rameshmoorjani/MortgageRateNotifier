"""
Knowledge Base Manager - Handles financial documents and vector embeddings.

Manages:
- Financial document storage
- Vector embeddings
- Semantic search
- Document retrieval
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import logging

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
except ImportError:
    print("Warning: scikit-learn not installed. Install with: pip install scikit-learn")
    TfidfVectorizer = None


@dataclass
class Document:
    """A financial document for the knowledge base."""
    id: str
    title: str
    content: str
    category: str  # mortgage_rates, refinancing, fha, conventional, etc.
    source: str
    date_added: str
    relevance_score: float = 0.0


@dataclass
class RetrievalResult:
    """Result of document retrieval."""
    documents: List[Document]
    query: str
    scores: List[float]
    timestamp: str


class KnowledgeBase:
    """
    Manages financial knowledge base with document storage and retrieval.
    """
    
    def __init__(self, documents_dir: str = "data/financial_documents"):
        """
        Initialize knowledge base.
        
        Args:
            documents_dir: Directory containing financial documents
        """
        self.documents_dir = Path(documents_dir)
        self.documents: Dict[str, Document] = {}
        self.vectorizer = None
        self.vectors = None
        self.logger = logging.getLogger("KnowledgeBase")
        
        # Create documents directory if it doesn't exist
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing documents
        self._load_documents()
    
    def add_document(self, doc: Document) -> None:
        """
        Add document to knowledge base.
        
        Args:
            doc: Document to add
        """
        self.documents[doc.id] = doc
        self.logger.info(f"Added document: {doc.title}")
        self._save_document(doc)
    
    def add_documents_batch(self, docs: List[Document]) -> None:
        """
        Add multiple documents.
        
        Args:
            docs: List of documents
        """
        for doc in docs:
            self.add_document(doc)
    
    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query string
            top_k: Number of documents to retrieve
            
        Returns:
            RetrievalResult with ranked documents
        """
        if not self.documents:
            self.logger.warning("Knowledge base is empty")
            return RetrievalResult([], query, [], datetime.now().isoformat())
        
        # If TfidfVectorizer available, use it; otherwise use simple keyword matching
        if TfidfVectorizer:
            return self._retrieve_tfidf(query, top_k)
        else:
            return self._retrieve_keyword(query, top_k)
    
    def _retrieve_tfidf(self, query: str, top_k: int) -> RetrievalResult:
        """Retrieve using TF-IDF vectorization."""
        try:
            # Prepare documents for vectorization
            doc_list = list(self.documents.values())
            texts = [doc.content[:1000] for doc in doc_list]  # Use first 1000 chars
            
            # Vectorize
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            doc_vectors = vectorizer.fit_transform(texts)
            query_vector = vectorizer.transform([query])
            
            # Calculate similarity
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            
            # Get top-k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = [doc_list[i] for i in top_indices]
            scores = [float(similarities[i]) for i in top_indices]
            
            return RetrievalResult(
                documents=results,
                query=query,
                scores=scores,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            self.logger.error(f"TF-IDF retrieval failed: {e}")
            return self._retrieve_keyword(query, top_k)
    
    def _retrieve_keyword(self, query: str, top_k: int) -> RetrievalResult:
        """Retrieve using simple keyword matching."""
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in self.documents.values():
            content_words = set(doc.content.lower().split())
            # Score based on keyword overlap
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / max(len(query_words), len(content_words))
                scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k
        results = [doc for doc, _ in scored_docs[:top_k]]
        scores = [score for _, score in scored_docs[:top_k]]
        
        return RetrievalResult(
            documents=results,
            query=query,
            scores=scores,
            timestamp=datetime.now().isoformat()
        )
    
    def _load_documents(self) -> None:
        """Load documents from disk."""
        doc_files = list(self.documents_dir.glob("*.json"))
        for file in doc_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    doc = Document(**data)
                    self.documents[doc.id] = doc
            except Exception as e:
                self.logger.error(f"Failed to load {file}: {e}")
    
    def _save_document(self, doc: Document) -> None:
        """Save document to disk."""
        try:
            file_path = self.documents_dir / f"{doc.id}.json"
            with open(file_path, 'w') as f:
                json.dump({
                    'id': doc.id,
                    'title': doc.title,
                    'content': doc.content,
                    'category': doc.category,
                    'source': doc.source,
                    'date_added': doc.date_added
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save document: {e}")
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        categories = {}
        for doc in self.documents.values():
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'categories': categories,
            'avg_content_length': sum(len(d.content) for d in self.documents.values()) / max(1, len(self.documents))
        }


# Sample financial documents
DEFAULT_DOCUMENTS = [
    Document(
        id="doc-mortgage-101",
        title="Understanding Mortgage Refinancing",
        content="""
        Mortgage refinancing is the process of replacing your current mortgage with a new one,
        typically at a lower interest rate. This can help you save money over time.
        
        Key benefits of refinancing:
        - Lower monthly payments
        - Reduction in total interest paid
        - Shortening loan term
        - Switching from ARM to fixed rate
        
        Costs to consider:
        - Origination fees (typically 0.5-1% of loan amount)
        - Appraisal fees ($300-700)
        - Title search and insurance
        - Closing costs (typically 2-5% of loan amount)
        
        Break-even analysis: Divide refinancing costs by monthly savings to find break-even months.
        For example, if costs are $5,000 and savings are $200/month, break-even is 25 months.
        """,
        category="refinancing",
        source="Federal Reserve",
        date_added=datetime.now().isoformat()
    ),
    Document(
        id="doc-rates-factors",
        title="Factors Affecting Mortgage Rates",
        content="""
        Mortgage interest rates are influenced by multiple economic factors:
        
        Federal Funds Rate: Set by the Federal Reserve, this is the primary driver of mortgage rates.
        When the Fed raises rates, mortgage rates typically increase within days or weeks.
        
        Economic Indicators:
        - Inflation: Higher inflation often leads to higher mortgage rates
        - Employment data: Strong job market can push rates up
        - GDP growth: Economic expansion affects rate trends
        - Housing starts: New construction activity influences rates
        
        Market Conditions:
        - Loan-to-value (LTV) ratio
        - Debt-to-income (DTI) ratio
        - Credit score
        - Loan term length (15yr vs 30yr)
        
        Current trends (2024-2026):
        - Rates have stabilized after 2023 increases
        - 30-year mortgages typically 0.5-1.0% above 15-year rates
        - ARM loans 0.25-0.75% lower than fixed rate
        """,
        category="mortgage_rates",
        source="Federal Reserve Economic Data",
        date_added=datetime.now().isoformat()
    ),
    Document(
        id="doc-breakeven",
        title="Calculating Break-Even on Refinancing",
        content="""
        Break-even analysis helps you determine if refinancing makes financial sense.
        
        Step 1: Calculate total refinancing costs
        - Origination fee: (Loan amount × 0.5-1.0%)
        - Appraisal: $300-700
        - Title and insurance: $200-500
        - Attorney (if applicable): $200-400
        - Recording fees: $50-150
        Total: Usually $3,000-$7,000 for a $300,000 loan
        
        Step 2: Calculate monthly savings
        New payment - Old payment = Monthly savings
        
        Step 3: Calculate break-even
        Refinancing costs ÷ Monthly savings = Break-even months
        
        Example:
        - Current payment: $1,500/month at 5.0%
        - Refinanced payment: $1,300/month at 4.0%
        - Monthly savings: $200
        - Refinancing costs: $5,000
        - Break-even: 25 months
        
        Rule of thumb: If break-even is less than 50% of remaining loan term, it's worth considering.
        """,
        category="refinancing",
        source="Consumer Financial Protection Bureau",
        date_added=datetime.now().isoformat()
    ),
    Document(
        id="doc-credit-impact",
        title="Impact of Refinancing on Credit Score",
        content="""
        Refinancing can affect your credit score in several ways:
        
        Initial impact (hard inquiry):
        - Hard credit inquiry: -5 to 10 points (temporary)
        - New account: Slight decrease initially
        - Recovery time: Usually 3-6 months
        
        Long-term benefits:
        - Lower utilization ratio (if debt consolidation involved)
        - More on-time payments with lower balance
        - Improved credit history diversity
        
        Avoiding negative impact:
        - Keep other accounts open
        - Don't apply for new credit immediately after
        - Make payments on time
        - Maintain low credit utilization (under 30%)
        
        Credit score minimums for refinancing:
        - Conventional loans: 620+ (but 740+ for best rates)
        - FHA loans: 580+
        - VA loans: 620+
        - USDA loans: 620+
        
        Note: Your credit score recovery is faster than you might think.
        Most borrowers see their score return to previous levels within 1-3 months.
        """,
        category="credit",
        source="Experian and FICO",
        date_added=datetime.now().isoformat()
    ),
    Document(
        id="doc-market-timing",
        title="Is Now a Good Time to Refinance?",
        content="""
        Market timing for refinancing depends on several factors:
        
        Rate environment indicators:
        - Rates falling: Good time to refinance (likely more room to fall)
        - Rates rising: Less favorable unless significant current savings
        - Rates stable: Consider if break-even is favorable
        
        Personal factors:
        - Time in home: Need to stay 25%+ of break-even point
        - Refinancing costs: Make sure savings justify costs
        - Credit score: Improved credit = better rates
        - Cash flow: Can you absorb closing costs?
        
        Historical context (2024-2026):
        - 30-year rates: 4.0-5.5% range (stabilized)
        - 15-year rates: 3.5-5.0% range
        - ARM rates: 3.0-4.5% for initial period
        
        Forecasting indicators:
        - Fed policy signals
        - Inflation trends
        - Economic growth expectations
        
        Recommendation: If rate drop is 0.5%+ and break-even < 25 months, strong candidate.
        If rate drop is 0.25-0.5%, only if break-even < 12 months.
        If rate drop < 0.25%, typically not worth it.
        """,
        category="market_timing",
        source="Mortgage Bankers Association",
        date_added=datetime.now().isoformat()
    )
]


def create_default_knowledge_base() -> KnowledgeBase:
    """Create knowledge base with default financial documents."""
    kb = KnowledgeBase()
    
    # Add default documents if empty
    if not kb.documents:
        kb.add_documents_batch(DEFAULT_DOCUMENTS)
        logging.getLogger("KnowledgeBase").info("Initialized with 5 default financial documents")
    
    return kb


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create knowledge base
    kb = create_default_knowledge_base()
    
    # Example queries
    queries = [
        "Should I refinance my mortgage?",
        "What affects mortgage interest rates?",
        "How do I calculate break-even for refinancing?",
        "Is my credit score good enough for refinancing?"
    ]
    
    print("Knowledge Base Stats:")
    print(kb.get_stats())
    print("\n" + "="*70)
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = kb.retrieve(query, top_k=2)
        for i, doc in enumerate(results.documents, 1):
            print(f"\n{i}. {doc.title} ({results.scores[i-1]:.2%} match)")
            print(f"   Category: {doc.category}")
            print(f"   Preview: {doc.content[:150]}...")
