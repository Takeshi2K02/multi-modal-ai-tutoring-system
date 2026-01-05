from typing import List, Dict, Any

# Mock Data Store
# Simulating a Vector DB with embedded chunks
MOCK_DOCUMENTS = [
    # Lecture 1: Basics
    {"id": "doc_001", "title": "Introduction to Vectors", "text": "A vector is a quantity having direction and magnitude. In linear algebra, we represent vectors as ordered lists of numbers.", "tags": ["vectors", "basics"], "topic": "Vectors & Geometry", "metadata": {"lecture_id": "L01", "week": 1, "page": 3, "lecture_title": "Foundations of Linear Algebra"}},
    {"id": "doc_002", "title": "Vector Addition and Scalar Multiplication", "text": "Vectors can be added component-wise. Scalar multiplication scales the magnitude of the vector without changing its direction.", "tags": ["vectors", "operations"], "topic": "Vectors & Geometry", "metadata": {"lecture_id": "L01", "week": 1, "page": 5, "lecture_title": "Foundations of Linear Algebra"}},
    {"id": "doc_003", "title": "The Dot Product", "text": "The dot product is an algebraic operation that takes two equal-length sequences of numbers and returns a single number.", "tags": ["vectors", "dot product"], "topic": "Vectors & Geometry", "metadata": {"lecture_id": "L01", "week": 1, "page": 8, "lecture_title": "Foundations of Linear Algebra"}},
    {"id": "doc_004", "title": "Vector Norms and Length", "text": "The length or magnitude of a vector is calculated using the Euclidean norm (L2 norm).", "tags": ["vectors", "norms"], "topic": "Vectors & Geometry", "metadata": {"lecture_id": "L01", "week": 1, "page": 12, "lecture_title": "Foundations of Linear Algebra"}},
    
    # Lecture 2: Matrices
    {"id": "doc_005", "title": "Introduction to Matrices", "text": "A matrix is a rectangular array of numbers arranged in rows and columns. Matrices are strictly used to represent linear maps.", "tags": ["matrices", "basics"], "topic": "Matrix Operations", "metadata": {"lecture_id": "L02", "week": 2, "page": 2, "lecture_title": "Matrix Theory"}},
    {"id": "doc_006", "title": "Matrix Addition and Multiplication", "text": "Matrix multiplication is not commutative. To multiply matrix A by B, the number of columns in A must equal the number of rows in B.", "tags": ["matrices", "operations"], "topic": "Matrix Operations", "metadata": {"lecture_id": "L02", "week": 2, "page": 6, "lecture_title": "Matrix Theory"}},
    {"id": "doc_007", "title": "The Transpose of a Matrix", "text": "Transposing a matrix swaps its rows and columns. The transpose of a product (AB)^T is B^T A^T.", "tags": ["matrices", "transpose"], "topic": "Matrix Operations", "metadata": {"lecture_id": "L02", "week": 2, "page": 9, "lecture_title": "Matrix Theory"}},
    {"id": "doc_008", "title": "Identity and Zero Matrices", "text": "The Identity matrix I leaves any vector unchanged when multiplied.", "tags": ["matrices", "special matrices"], "topic": "Matrix Operations", "metadata": {"lecture_id": "L02", "week": 2, "page": 11, "lecture_title": "Matrix Theory"}},
    {"id": "doc_009", "title": "Matrix Inversion", "text": "An invertible matrix A has an inverse A^-1 such that AA^-1 = I.", "tags": ["matrices", "inversion"], "topic": "Matrix Operations", "metadata": {"lecture_id": "L02", "week": 2, "page": 15, "lecture_title": "Matrix Theory"}},

    # Lecture 3: Systems
    {"id": "doc_010", "title": "Systems of Linear Equations", "text": "A system of linear equations can be represented as Ax = b.", "tags": ["systems", "equations"], "topic": "Linear Systems", "metadata": {"lecture_id": "L03", "week": 3, "page": 4, "lecture_title": "Solving Systems"}},
    {"id": "doc_011", "title": "Gaussian Elimination", "text": "Gaussian elimination is an algorithm for solving systems of linear equations.", "tags": ["systems", "gaussian elimination"], "topic": "Linear Systems", "metadata": {"lecture_id": "L03", "week": 3, "page": 7, "lecture_title": "Solving Systems"}},
    {"id": "doc_012", "title": "Row Echelon Form", "text": "A matrix is in row echelon form if all zero rows are at the bottom.", "tags": ["systems", "row reduction"], "topic": "Linear Systems", "metadata": {"lecture_id": "L03", "week": 3, "page": 10, "lecture_title": "Solving Systems"}},
    
    # Lecture 3 (Cont'd): Determinants
    {"id": "doc_013", "title": "The Determinant", "text": "The determinant is a scalar value characterizing a square matrix.", "tags": ["determinants", "singular"], "topic": "Determinants", "metadata": {"lecture_id": "L03", "week": 3, "page": 20, "lecture_title": "Solving Systems"}},
    {"id": "doc_014", "title": "Properties of Determinants", "text": "The determinant of a product is the product of determinants.", "tags": ["determinants", "properties"], "topic": "Determinants", "metadata": {"lecture_id": "L03", "week": 3, "page": 22, "lecture_title": "Solving Systems"}},

    # Lecture 4: Abstract Spaces
    {"id": "doc_015", "title": "Vector Spaces and Subspaces", "text": "A vector space is a set of objects (vectors) tailored with addition and scalar multiplication.", "tags": ["vector spaces", "theory"], "topic": "Vector Spaces", "metadata": {"lecture_id": "L04", "week": 4, "page": 2, "lecture_title": "Abstract Vector Spaces"}},
    {"id": "doc_016", "title": "Linear Independence", "text": "A set of vectors is linearly independent if no vector in the set can be defined as a linear combination of the others.", "tags": ["vector spaces", "independence"], "topic": "Vector Spaces", "metadata": {"lecture_id": "L04", "week": 4, "page": 5, "lecture_title": "Abstract Vector Spaces"}},
    {"id": "doc_017", "title": "Basis and Dimension", "text": "A basis is a linearly independent set that spans the vector space.", "tags": ["vector spaces", "basis", "dimension"], "topic": "Vector Spaces", "metadata": {"lecture_id": "L04", "week": 4, "page": 8, "lecture_title": "Abstract Vector Spaces"}},

    # Lecture 5: Maps
    {"id": "doc_018", "title": "Linear Transformations", "text": "A linear transformation is a mapping function between two vector spaces.", "tags": ["linear maps", "transformations"], "topic": "Linear Transformations", "metadata": {"lecture_id": "L05", "week": 5, "page": 3, "lecture_title": "Linear Maps"}},
    {"id": "doc_019", "title": "Kernel and Image", "text": "The Kernel (null space) is the set of vectors mapped to zero.", "tags": ["linear maps", "kernel", "image"], "topic": "Linear Transformations", "metadata": {"lecture_id": "L05", "week": 5, "page": 6, "lecture_title": "Linear Maps"}},
    {"id": "doc_020", "title": "Rank-Nullity Theorem", "text": "The Rank-Nullity theorem relates the dimensions of the kernel and image.", "tags": ["linear maps", "theorems"], "topic": "Linear Transformations", "metadata": {"lecture_id": "L05", "week": 5, "page": 9, "lecture_title": "Linear Maps"}},
]

def mock_vector_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Simulates a semantic search using simple keyword overlap scoring.
    """
    query_terms = set(query.lower().split())
    
    scored_docs = []
    
    for doc in MOCK_DOCUMENTS:
        # Simple scoring: +1 for title match, +0.5 for tag match, +0.1 for text match
        score = 0.0
        
        # Title match (Weight: High)
        title_lower = doc["title"].lower()
        for term in query_terms:
            if term in title_lower:
                score += 1.0
                
        # Tag match (Weight: Medium)
        for tag in doc["tags"]:
            for term in query_terms:
                if term in tag.lower():
                    score += 0.5
                    
        # Text match (Weight: Low)
        text_lower = doc["text"].lower()
        for term in query_terms:
            if term in text_lower:
                score += 0.1
                
        if score > 0:
            scored_docs.append({
                **doc,
                "score": round(score, 2)
            })
            
    # Sort by score desc
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_docs[:top_k]
