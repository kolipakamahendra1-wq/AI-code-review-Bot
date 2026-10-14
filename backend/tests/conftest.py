import pytest

from app import config

SAMPLE_DIFF = """diff --git a/app/auth.py b/app/auth.py
index 111..222 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,4 +10,8 @@ def login(user, pw):
     user = get(user)
+    query = "SELECT * FROM users WHERE name = '" + user + "'"
+    db.execute(query)
+    API_KEY = "sk-live-123456"
     return user

 def logout():
diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,2 +1,3 @@
 {
+  "x": 1,
 }
"""


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "ENABLE_RULES", False)  # tests opt in explicitly


@pytest.fixture
def sample_diff():
    return SAMPLE_DIFF
