import requests
import json
import re
import time

def predict_gender(name):
    """
    Predict gender using LM Studio API with improved parsing and fallback logic
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
                    "model": "llama4-dolphin-8b",  # Changed from qwen3-8b
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
                
                # Handle <think> tags like in ai_reply_helper.py
                if "<think>" in content and "</think>" in content:
                    last_think_end = content.rfind("</think>")
                    if last_think_end != -1:
                        content = content[last_think_end + 8:].strip()  # +8 for "</think>"
                
                # Clean up the response
                content = content.lower().strip()
                
                # Simple keyword matching
                if 'male' in content and 'female' not in content:
                    return 'm'
                elif 'female' in content:
                    return 'f'
                    
            break  # Exit retry loop if we got a response
            
        except Exception as e:
            print(f"API error for '{first_name}' (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
    
    # Very simple and direct prompt
    prompt = f"Gender of name {first_name}: male or female?"
    
    try:
        response = requests.post(
            "http://127.0.0.1:4999/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen3-8b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,  # Most deterministic
                "max_tokens": 5,     # Very short response
                "stop": ["\n", ".", "!", "?"]  # Stop at punctuation
            },
            timeout=10  # Shorter timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip().lower()
            
            print(f"Debug - Raw response for '{first_name}': '{content}'")
            
            # Simple keyword matching
            if 'male' in content and 'female' not in content:
                return 'm'
            elif 'female' in content:
                return 'f'
            
    except Exception as e:
        print(f"API error for '{first_name}': {e}")
    
    # Enhanced fallback logic with better name patterns
    first_name_lower = first_name.lower()
    
    # Common male name patterns and endings
    male_patterns = {
        # Common male names
        'alexander', 'andrew', 'anthony', 'benjamin', 'charles', 'christopher', 'daniel', 'david',
        'edward', 'frank', 'george', 'henry', 'james', 'john', 'joseph', 'kenneth', 'mark',
        'matthew', 'michael', 'paul', 'peter', 'richard', 'robert', 'thomas', 'william',
        'juan', 'carlos', 'luis', 'miguel', 'antonio', 'francisco', 'jose', 'manuel',
        'petr', 'pavel', 'jan', 'tomas', 'martin', 'karel', 'jakub', 'lukas',
        # Previously added names:
        'roman', 'adam', 'dominik', 'mahmoud', 'miroslav', 'lukáš',
        # User corrections from na_names.txt:
        'dmitry', 'giovanni', 'ian', 'jaroslav', 'jiri', 'jonathan', 'marek', 'samuel', 'tony',
        'árpád', 'štěpán', 'marco',  # Normalized special characters
        # Male endings (but be careful with exceptions)
        'o', 'os', 'us', 'is', 'es'
    }
    
    # Female name patterns and endings
    female_patterns = {
        # Common female names
        'maria', 'ana', 'carmen', 'laura', 'patricia', 'jennifer', 'linda', 'elizabeth',
        'barbara', 'susan', 'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty',
        'helen', 'sandra', 'donna', 'carol', 'ruth', 'sharon', 'michelle', 'emily',
        'adelia', 'urmila', 'priya', 'kavya', 'anita', 'sunita', 'geeta', 'rita',
        # Previously added names:
        'eve', 'nina', 'olena', 'юлия', 'deborah', 'celine', 'barbs',
        # User corrections from na_names.txt:
        'alice', 'annemette', 'dituš', 'lucie', 'mary', 'natali', 'stephanie', 'susane',
        # Russian/Cyrillic female names:
        'валерия', 'даяна', 'маргарита', 'нонна',
        # Female endings
        'ova', 'eva', 'ina', 'ika', 'anka'
    }
    
    # Check exact name matches first
    if first_name_lower in male_patterns:
        print(f"Debug - Exact male name match for '{first_name}'")
        return 'm'
    
    if first_name_lower in female_patterns:
        print(f"Debug - Exact female name match for '{first_name}'")
        return 'f'
    
    # Check endings (with exceptions)
    if len(first_name_lower) > 2:
        # Female endings (but exclude known male names)
        if (first_name_lower.endswith('a') and 
            first_name_lower not in {'joshua', 'luca', 'andrea'}):
            print(f"Debug - Female ending 'a' for '{first_name}'")
            return 'f'
        
        if first_name_lower.endswith(('ia', 'ina', 'ika', 'ova')):
            print(f"Debug - Female ending pattern for '{first_name}'")
            return 'f'
        
        # Male endings
        if first_name_lower.endswith(('o', 'os', 'us', 'is', 'es')):
            print(f"Debug - Male ending pattern for '{first_name}'")
            return 'm'
    
    print(f"Debug - Cannot determine gender for '{first_name}'")
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
            if len(parts) >= 6:  # Should have gender as last field (index 5)
                name_field = parts[3].strip()
                gender = parts[5].strip()  # Changed from parts[4] to parts[5]
                
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
            
            # Split by colon and get the 4th field (index 3)
            parts = line.split(':')
            if len(parts) >= 4:
                name_field = parts[3].strip()
                
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
    process_names('names.txt', 'names_with_gender.txt')