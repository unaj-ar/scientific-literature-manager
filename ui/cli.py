from services.literature_service import LiteratureService


class CLIInterface:
    def __init__(self):
        self.service = LiteratureService()

    def add_article_view(self):
        print("\n--- ADD NEW ARTICLE ---")
        title = input("Title: ")
        authors = input("Authors (comma-separated, e.g., 'John Doe, Jane Smith'): ")
        year = input("Publication Year: ")
        doi = input("DOI: ")
        priority = input("Priority (P1=High, P2=Medium, P3=Low) [P2]: ")
        status = input("Status (Unread, In Progress, Read, Archived) [Unread]: ")
        tags = input("Tags (comma-separated): ")
        pdf_path = input("PDF Path or Link: ")
        notes = input("Initial Notes / Summary: ")

        try:
            article_id = self.service.register_new_article(
                title, authors, year, doi, priority, status, tags, pdf_path, notes
            )
            print(f"✅ Article successfully saved with ID: {article_id}")
        except Exception as e:
            print(f"⚠️ Error adding article: {e}")

    def list_priority_view(self):
        print("\n--- PRIORITIZED READING LIST ---")
        articles = self.service.fetch_prioritized_list()
        if not articles:
            print("No articles registered yet.")
            return

        for art in articles:
            authors_str = art['authors'] if art['authors'] else 'No authors'
            print(
                f"[{art['priority']}] ID: {art['id']} | {art['title']} | Authors: {authors_str} | Status: {art['status']}")

    def search_by_author_view(self):
        print("\n--- GET ARTICLES BY AUTHOR ---")
        author_name = input("Enter author's name: ")
        articles = self.service.fetch_articles_by_author(author_name)

        if not articles:
            print(f"No articles found for author matching: '{author_name}'")
            return

        print(f"\nFound {len(articles)} article(s):")
        for art in articles:
            print("-" * 50)
            print(f"ID: {art['id']} | [{art['priority']}] {art['title']} ({art['publication_year'] or 'N/A'})")
            print(f"Status: {art['status']} | DOI: {art['doi']}")
            print(f"PDF Link: {art['pdf_path']}")

    def start(self):
        while True:
            print("\n=== SCIENTIFIC LITERATURE MANAGER ===")
            print("1. Add Article (Discovery)")
            print("2. View Priority List (Prioritization)")
            print("3. Get Articles by Author")
            print("4. Exit")

            choice = input("Select an option (1-4): ")
            if choice == '1':
                self.add_article_view()
            elif choice == '2':
                self.list_priority_view()
            elif choice == '3':
                self.search_by_author_view()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")