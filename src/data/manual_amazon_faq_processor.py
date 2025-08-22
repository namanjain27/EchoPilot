"""
Manual Amazon FAQ Processor
This script processes FAQ data that has been manually copied from the Amazon IR FAQ page.
Use this when the automated scraper is blocked by the website.
"""

import json
import os
from datetime import datetime


class ManualFAQProcessor:
    def __init__(self):
        self.faqs = []

    def process_text_input(self, text_content):
        """Process manually copied text content"""
        lines = text_content.strip().split('\n')
        current_question = ""
        current_answer = ""
        in_answer = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line looks like a question (contains '?' and is substantial)
            if '?' in line and len(line) > 15 and not in_answer:
                # Save previous Q&A if exists
                if current_question and current_answer:
                    self.faqs.append({
                        'question': current_question.strip(),
                        'answer': current_answer.strip()
                    })
                
                current_question = line
                current_answer = ""
                in_answer = True
                
            elif in_answer and line and not ('?' in line and len(line) > 15):
                # This is part of an answer
                current_answer += line + " "
        
        # Add the last Q&A
        if current_question and current_answer:
            self.faqs.append({
                'question': current_question.strip(),
                'answer': current_answer.strip()
            })
        
        print(f"Processed {len(self.faqs)} FAQ items from manual input")
        return len(self.faqs) > 0

    def load_from_file(self, file_path):
        """Load FAQ text from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.process_text_input(content)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    def generate_documents(self, output_prefix="amazon_faqs"):
        """Generate both text and JSON documents"""
        if not self.faqs:
            print("No FAQs to generate documents from")
            return False

        # Generate text document
        txt_filename = f"{output_prefix}.txt"
        content = "Amazon Investor Relations - Frequently Asked Questions\n"
        content += "=" * 60 + "\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Total Questions: {len(self.faqs)}\n"
        content += "=" * 60 + "\n\n"
        
        for i, faq in enumerate(self.faqs, 1):
            content += f"Q{i}: {faq['question']}\n"
            content += "-" * 50 + "\n"
            content += f"A: {faq['answer']}\n\n"
        
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Text document generated: {txt_filename}")

        # Generate JSON document
        json_filename = f"{output_prefix}.json"
        json_data = {
            'title': 'Amazon Investor Relations - Frequently Asked Questions',
            'generated_on': datetime.now().isoformat(),
            'total_count': len(self.faqs),
            'faqs': self.faqs
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"JSON document generated: {json_filename}")

        return True

    def interactive_input(self):
        """Interactive method to manually input FAQ data"""
        print("Interactive FAQ Input Mode")
        print("Enter FAQ questions and answers. Type 'done' when finished.")
        print("-" * 50)
        
        while True:
            question = input("Enter question (or 'done' to finish): ").strip()
            if question.lower() == 'done':
                break
            
            if not question:
                continue
                
            answer = input("Enter answer: ").strip()
            
            if question and answer:
                self.faqs.append({
                    'question': question,
                    'answer': answer
                })
                print(f"Added FAQ #{len(self.faqs)}")
            
        return len(self.faqs) > 0


def main():
    processor = ManualFAQProcessor()
    
    print("Amazon FAQ Manual Processor")
    print("=" * 40)
    print("Options:")
    print("1. Load from file (paste FAQ text in a file)")
    print("2. Interactive input")
    print("3. Use sample data for testing")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        file_path = input("Enter file path: ").strip()
        if processor.load_from_file(file_path):
            processor.generate_documents()
        else:
            print("Failed to process file")
    
    elif choice == "2":
        if processor.interactive_input():
            processor.generate_documents()
        else:
            print("No FAQs entered")
    
    elif choice == "3":
        # Sample data for testing
        sample_faqs = [
            {
                'question': 'What is Amazon\'s business model?',
                'answer': 'Amazon operates multiple business segments including e-commerce, cloud computing (AWS), advertising, and digital streaming services.'
            },
            {
                'question': 'How does Amazon report its financial results?',
                'answer': 'Amazon reports quarterly earnings with detailed breakdowns of revenue by segment, including North America, International, and AWS.'
            },
            {
                'question': 'What are Amazon\'s key growth drivers?',
                'answer': 'Key growth drivers include AWS expansion, advertising services, Prime membership growth, and international market expansion.'
            }
        ]
        
        processor.faqs = sample_faqs
        print("Loaded sample FAQ data for testing")
        processor.generate_documents("sample_amazon_faqs")
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()