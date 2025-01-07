from fastapi import FastAPI

app = FastAPI()

print("=== TOP-LEVEL PRINT ===")


@app.get("/dummy-test")
def dummy_test():
    print("=== INSIDE dummy_test ===")
    return {"hello": "world"}
