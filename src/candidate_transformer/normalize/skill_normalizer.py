"""Skill name canonicalization."""

from __future__ import annotations

import re

CANONICAL_SKILLS: dict[str, str] = {
    "python": "Python",
    "py": "Python",
    "python3": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "react": "React",
    "reactjs": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "git": "Git",
    "linux": "Linux",
    "html": "HTML",
    "css": "CSS",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
    "rest": "REST APIs",
    "graphql": "GraphQL",
    "kafka": "Apache Kafka",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
}


def canonicalize_skill(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    key = re.sub(r"[^a-z0-9+#.\s-]", "", str(raw).lower()).strip()
    key = re.sub(r"\s+", " ", key)
    if not key:
        return None
    if key in CANONICAL_SKILLS:
        return CANONICAL_SKILLS[key]
    for alias, canonical in CANONICAL_SKILLS.items():
        if alias == key:
            return canonical
    return key.title()


def canonicalize_skills(raw_skills: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in raw_skills:
        canonical = canonicalize_skill(raw)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result
