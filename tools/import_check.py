import traceback
import sys


def main():
  import os
  project_root = os.path.abspath(os.path.join(os.getcwd(), '..')) if os.path.basename(
      os.getcwd()).lower() == 'tools' else os.getcwd()
  # ensure project root is on sys.path so 'app' package resolves
  if project_root not in sys.path:
    sys.path.insert(0, project_root)
  print('cwd=', os.getcwd())
  print('project_root=', project_root)
  print('sys.path[0]=', sys.path[0])
  print('sys.path sample=', sys.path[:5])
  try:
    import app
    print('OK')
  except Exception:
    traceback.print_exc()
    sys.exit(1)


if __name__ == '__main__':
  main()
