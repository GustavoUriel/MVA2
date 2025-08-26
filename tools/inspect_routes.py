from app import create_app

app = create_app()

with app.test_request_context():
  rules = sorted([(r.rule, r.endpoint) for r in app.url_map.iter_rules()])
  for rule, endpoint in rules:
    print(rule, '->', endpoint)
