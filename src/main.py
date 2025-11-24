"""Main entry point for AutoRBI application."""

try:
    
    from .app import AutoRBIApp
except ImportError:
    
    from app import AutoRBIApp


def main() -> None:
    """Run the AutoRBI application."""
    app = AutoRBIApp()
    app.mainloop()


if __name__ == "__main__":
    main()

