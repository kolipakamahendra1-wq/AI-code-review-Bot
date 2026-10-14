export const SAMPLES = {
  "Python login": `diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,4 +10,9 @@ def login(user, pw):
     user = get(user)
+    query = "SELECT * FROM users WHERE name = '" + user + "'"
+    rows = db.execute(query)
+    API_KEY = "sk-live-9f8e7d6c5b4a"
+    try:
+        verify(rows, pw)
+    except:
+        pass
     return user
`,
  "React widget": `diff --git a/src/Comment.jsx b/src/Comment.jsx
--- a/src/Comment.jsx
+++ b/src/Comment.jsx
@@ -1,3 +1,8 @@
 export function Comment({ text }) {
+  console.log("rendering", text);
+  return <div dangerouslySetInnerHTML={{ __html: text }} />;
+}
+
+export async function load(url) {
+  return fetch(url, { agent: new https.Agent({ rejectUnauthorized: false }) });
 }
`,
  "Shell runner": `diff --git a/tools/run.py b/tools/run.py
--- a/tools/run.py
+++ b/tools/run.py
@@ -1,2 +1,7 @@
 import subprocess
+
+def run(cmd, expr):
+    subprocess.run(cmd, shell=True)
+    return eval(expr)  # TODO: remove
`,
};
