import requests
import re
import time
import random
import json
import os
from urllib.parse import urljoin
from html import unescape


class AmazonFAQScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        self.faqs = []

    def fetch_page_with_retry(self, url, max_retries=3, delay_range=(1, 3)):
        """Fetch page with retry mechanism and random delays"""
        for attempt in range(max_retries):
            try:
                delay = random.uniform(*delay_range)
                time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"Access forbidden (403). Attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * 2)  # Longer delay for 403
                else:
                    print(f"HTTP {response.status_code}. Attempt {attempt + 1}/{max_retries}")
                    
            except requests.RequestException as e:
                print(f"Request failed: {e}. Attempt {attempt + 1}/{max_retries}")
                
            if attempt < max_retries - 1:
                time.sleep(delay * 2)
        
        return None

    def extract_faqs_from_html(self, html_content):
        """Extract FAQ data from HTML content using regex patterns"""
        faqs_found = []
        
        # Clean HTML and convert to text
        html_text = html_content.decode('utf-8') if isinstance(html_content, bytes) else html_content
        
        # Remove script and style elements
        html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Pattern 1: Look for FAQ-like structures
        faq_patterns = [
            # Pattern for FAQ items with question/answer structure
            r'<[^>]*class[^>]*faq[^>]*>.*?</[^>]*>',
            r'<[^>]*id[^>]*faq[^>]*>.*?</[^>]*>',
            
            # Pattern for question-answer pairs
            r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',
            
            # Pattern for heading followed by paragraphs
            r'<h[3-6][^>]*>(.*?\?.*?)</h[3-6]>\s*<p[^>]*>(.*?)</p>',
            
            # Pattern for accordion-style content
            r'<[^>]*class[^>]*accordion[^>]*>.*?</[^>]*>',
        ]
        
        # Extract content using patterns
        for pattern in faq_patterns:
            matches = re.findall(pattern, html_text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    question = self.clean_html_text(match[0])
                    answer = self.clean_html_text(match[1])
                    
                    if question and len(question) > 10 and '?' in question:
                        faqs_found.append({
                            'question': question,
                            'answer': answer if answer else "Answer not found"
                        })
        
        # If no structured FAQs found, look for any text with question marks
        if not faqs_found:
            # Extract all text content and look for Q&A patterns
            text_content = re.sub(r'<[^>]+>', ' ', html_text)
            text_content = unescape(text_content)
            
            # Split by common separators and look for questions
            lines = re.split(r'\n|\r\n|\r', text_content)
            current_question = ""
            current_answer = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line looks like a question
                if '?' in line and len(line) > 20:
                    if current_question and current_answer:
                        faqs_found.append({
                            'question': current_question,
                            'answer': current_answer
                        })
                    current_question = line
                    current_answer = ""
                elif current_question and len(line) > 20:
                    current_answer += line + " "
            
            # Add the last Q&A if exists
            if current_question and current_answer:
                faqs_found.append({
                    'question': current_question,
                    'answer': current_answer.strip()
                })
        
        return faqs_found

    def clean_html_text(self, html_text):
        """Clean HTML tags and entities from text"""
        if not html_text:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        
        # Decode HTML entities
        clean_text = unescape(clean_text)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text

    def scrape_faqs(self, url):
        """Main scraping method"""
        print(f"Attempting to scrape FAQs from: {url}")
        
        response = self.fetch_page_with_retry(url)
        if not response:
            print("Failed to fetch the page after multiple attempts")
            return False
        
        print("Successfully fetched the page")
        
        # Extract FAQs
        faqs = self.extract_faqs_from_html(response.content)
        
        if faqs:
            self.faqs = faqs
            print(f"Successfully extracted {len(faqs)} FAQ items")
            return True
        else:
            print("No FAQs found. The page structure might be different than expected.")
            # Save raw HTML for manual inspection
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved raw HTML to 'debug_page.html' for manual inspection")
            return False

    def generate_document(self, output_filename="amazon_faqs.txt"):
        """Generate text document from extracted FAQs"""
        if not self.faqs:
            print("No FAQs to generate document from")
            return False
        
        print(f"Generating text document with {len(self.faqs)} FAQ items...")
        
        # Create content
        content = "Amazon Investor Relations - Frequently Asked Questions\n"
        content += "=" * 60 + "\n\n"
        
        # Add FAQs
        for i, faq in enumerate(self.faqs, 1):
            content += f"Q{i}: {faq['question']}\n"
            content += "-" * 40 + "\n"
            content += f"A: {faq['answer']}\n\n"
            content += "\n"
        
        # Save document
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Text document generated successfully: {output_filename}")
        
        # Also create a JSON version for structured data
        json_filename = output_filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'title': 'Amazon Investor Relations - Frequently Asked Questions',
                'faqs': self.faqs,
                'total_count': len(self.faqs)
            }, f, indent=2, ensure_ascii=False)
        
        print(f"JSON document also generated: {json_filename}")
        return True

    def run(self, url, output_filename="amazon_faqs.txt"):
        """Run the complete scraping and document generation process"""
        success = self.scrape_faqs(url)
        if success:
            return self.generate_document(output_filename)
        return False


def main():
    """Main function to run the scraper"""
    url = "https://ir.aboutamazon.com/faqs/default.aspx"
    scraper = AmazonFAQScraper()
    
    success = scraper.run(url)
    
    if success:
        print("✓ FAQ scraping and document generation completed successfully!")
    else:
        print("✗ Failed to scrape FAQs. Please check the debug output.")


if __name__ == "__main__":
    main()