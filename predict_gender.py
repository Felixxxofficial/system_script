import requests
import json
import re
import time
import sys

def test_lm_studio_connection():
    """
    Test connection to LM Studio API before processing
    """
    print("Testing LM Studio connection...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:4999/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "llama4-dolphin-8b",
                "messages": [
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'test'"}
                ],
                "temperature": 0.0,
                "max_tokens": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                print("✅ LM Studio connection successful!")
                print(f"Model response: {result['choices'][0]['message']['content'].strip()}")
                return True
            else:
                print("❌ LM Studio responded but with unexpected format")
                return False
        else:
            print(f"❌ LM Studio connection failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LM Studio. Make sure it's running on http://127.0.0.1:4999")
        return False
    except requests.exceptions.Timeout:
        print("❌ LM Studio connection timed out")
        return False
    except Exception as e:
        print(f"❌ LM Studio connection test failed: {e}")
        return False

def predict_gender(name):
    """
    Predict gender using LM Studio API only (no fallback)
    """
    # Clean the name - remove emojis and extra characters
    clean_name = re.sub(r'[^\w\s]', '', name).strip()
    first_name = clean_name.split()[0] if clean_name.split() else name
    
    # Try API with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://127.0.0.1:4999/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "llama4-dolphin-8b",
                    "messages": [
                        {"role": "system", "content": "You are a gender classification assistant. Respond with only 'male' or 'female' for the given name."},
                        {"role": "user", "content": f"What is the gender of the name '{first_name}'?"}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 10,
                    "stop": ["\n", ".", "!", "?"]
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                print(f"Debug - Raw response for '{first_name}': '{content}'")
                
                # Handle <think> tags
                if "<think>" in content and "</think>" in content:
                    last_think_end = content.rfind("</think>")
                    if last_think_end != -1:
                        content = content[last_think_end + 8:].strip()
                
                # Clean up the response
                content = content.lower().strip()
                
                # Simple keyword matching
                if 'male' in content and 'female' not in content:
                    return 'm'
                elif 'female' in content:
                    return 'f'
                else:
                    print(f"Warning - Unclear response for '{first_name}': '{content}'")
                    return 'na'
                    
            break  # Exit retry loop if we got a response
            
        except Exception as e:
            print(f"API error for '{first_name}' (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to get response for '{first_name}' after {max_retries} attempts")
                return 'na'
    
    return 'na'

def create_categorized_files(output_file):
    """
    Create separate files for male, female, and 'na' names from the results
    """
    male_names = []
    female_names = []
    na_names = []
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(':')
            if len(parts) >= 6:
                name_field = parts[3].strip()
                gender = parts[5].strip()
                
                # Extract first name for categorization
                clean_name = re.sub(r'[^\w\s]', '', name_field).strip()
                first_name = clean_name.split()[0] if clean_name.split() else name_field
                
                if gender == 'm':
                    male_names.append(first_name)
                elif gender == 'f':
                    female_names.append(first_name)
                else:  # 'na'
                    na_names.append(first_name)
        
        # Write categorized files
        with open('male_names.txt', 'w', encoding='utf-8') as f:
            for name in sorted(set(male_names)):
                f.write(name + '\n')
        
        with open('female_names.txt', 'w', encoding='utf-8') as f:
            for name in sorted(set(female_names)):
                f.write(name + '\n')
        
        with open('na_names.txt', 'w', encoding='utf-8') as f:
            for name in sorted(set(na_names)):
                f.write(name + '\n')
        
        print(f"\nCategorized files created:")
        print(f"- male_names.txt: {len(set(male_names))} unique names")
        print(f"- female_names.txt: {len(set(female_names))} unique names")
        print(f"- na_names.txt: {len(set(na_names))} unique names")
        
    except Exception as e:
        print(f"Error creating categorized files: {e}")

def process_names(input_file, output_file):
    """
    Process names from colon-separated file and add gender predictions
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        processed_lines = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Split by colon and get the 5th field (index 4) - the name field
            parts = line.split(':')
            if len(parts) >= 5:  # Changed from >= 4 to >= 5
                name_field = parts[4].strip()  # Changed from parts[3] to parts[4]
                
                # Extract first name for gender prediction
                clean_name = re.sub(r'[^\w\s]', '', name_field).strip()
                first_name = clean_name.split()[0] if clean_name.split() else name_field
                
                if first_name:
                    print(f"Processing {i}/{total_lines}: {first_name}")
                    gender = predict_gender(first_name)
                    print(f"Name: {name_field} -> First name: {first_name}, Gender: {gender}")
                    
                    # Add gender as new field
                    new_line = line + ':' + gender
                    processed_lines.append(new_line)
                    
                    # Small delay to be respectful to the API
                    time.sleep(0.2)
                else:
                    print(f"Skipping line {i}: No valid name found")
                    processed_lines.append(line + ':na')
            else:
                print(f"Skipping line {i}: Not enough fields")
                processed_lines.append(line + ':na')
            
            print()  # Empty line for readability
        
        # Write results
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in processed_lines:
                f.write(line + '\n')
        
        print(f"Processing complete! Results saved to {output_file}")
        print(f"Processed {len(processed_lines)} lines")
        
        # Create categorized files
        create_categorized_files(output_file)
        
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    # Test LM Studio connection first
    if not test_lm_studio_connection():
        print("\n🛑 Exiting: LM Studio connection failed. Please start LM Studio and load the model first.")
        sys.exit(1)
    
    print("\n🚀 Starting name processing...\n")
    process_names('names.txt', 'names_with_gender.txt')