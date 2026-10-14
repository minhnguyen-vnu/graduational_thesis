import sys, math
exec(open("b3check.py").read().rsplit("for rep, fl in", 1)[0])
w, prior = vtrain(ops)
for key in ("username", "login", "userName", "user_name", "name", "owner", "createdBy", "author", "email", "title", "displayName", "assignee"):
    f = {"kind": "str", "loc": "body", "leaf": key.lower(), "raw_leaf": key, "name": key, "enum": []}
    s = prior + sum(w.get(t, 0.0) for t in ffeats(f))
    print("%-12s score %+.2f  p=%.0f%%" % (key, s, 100 / (1 + math.exp(-s))))
