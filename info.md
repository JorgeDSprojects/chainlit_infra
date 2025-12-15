.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
http://localhost:8000/chat
http://localhost:8000/docs

{
  "email": "test@test.com",
  "password": "123"
}
