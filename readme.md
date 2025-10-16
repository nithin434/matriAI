curl "http://127.0.0.1:8000/health"

curl -X POST "http://127.0.0.1:8000/users" -H "Content-Type: application/json" -d "{\"Age\": 29, \"Gender\": \"Female\", \"Marital_Status\": \"Never Married\", \"Caste\": \"Syed\", \"Sect\": \"Sunni\", \"State\": \"Maharashtra\", \"About\": \"Software engineer, enjoys books and travel\", \"Partner_Preference\": \"Looking for educated caring partner from good family\"}"


curl "http://127.0.0.1:8000/match?query=Looking%20for%20educated%20caring%20partner&gender=Male&min_age=24&max_age=32&caste=Syed&state=Maharashtra&top_k=10"

curl "http://127.0.0.1:8000/match?user_id=USER_ID_HERE&top_k=10"

curl "http://127.0.0.1:8000/match?user_id=USER_ID_HERE&same_gender=true&top_k=10"

curl "http://127.0.0.1:8000/match?query=educated%20partner%20from%20good%20family&gender=Male&caste=Syed&sect=Sunni&state=Maharashtra&marital_status=Never%20Married&min_age=24&max_age=32&top_k=10"

curl "http://127.0.0.1:8000/match?user_id=USER_ID_HERE&age_tolerance=5&top_k=10"


##Above are the curl request to test or use use /docs

And run the embeding.py to load the indexes for the RAG system(it will take time if you try to load 300k users)
So, try embeddings.py --limit 5000

ANd run main.py to run the system. Before it setup the bothdb's(mongodb, chromadb)

