from app import create_app

app = create_app()

with app.app_context():
  rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
  for r in rules:
    methods = ','.join(sorted(list(r.methods - {"HEAD", "OPTIONS"})))
    print(f"{r.rule:40}  {methods:20}  -> {r.endpoint}")
