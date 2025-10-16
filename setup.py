from setuptools import setup, find_packages

setup(
    name="aimat-rag-system",
    version="0.2.0",
    description="RAG system with MongoDB (scalar) + ChromaDB (vector) for user matching",
    packages=find_packages(exclude=["tests", "examples"]),
    py_modules=["import_users", "analyze_users", "create_indexes", "embeddings", "search"],
    install_requires=[
        "pymongo>=4.3",
        "langchain>=0.1.0",
        "langchain-google-genai>=1.0.0",
        "langchain-chroma>=0.1.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
    ],
    entry_points={
        "console_scripts": [
            "import-users=import_users:main",
            "analyze-users=analyze_users:main",
            "create-indexes=create_indexes:main",
            "generate-embeddings=embeddings:main",
            "search-users=search:main",
        ]
    },
    python_requires=">=3.8",
)
