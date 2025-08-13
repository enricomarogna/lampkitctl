def main():
    from .cli import main as _main
    return _main()

if __name__ == "__main__":
    raise SystemExit(main())
