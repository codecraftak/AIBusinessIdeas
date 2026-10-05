import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import zlib
import base64
import uuid

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
EMAIL_SENDER = os.getenv("EMAIL_SENDER") or "aksh0576@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or ""
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT") or "aksh0576@gmail.com"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing or empty. Please set it in your environment or GitHub Secrets.")
if not EMAIL_PASSWORD:
    raise ValueError("EMAIL_PASSWORD is missing or empty. Please set it in your environment or GitHub Secrets.")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

genai.configure(api_key=GEMINI_API_KEY)

def load_history():
    if os.path.exists("ideas_history.json"):
        with open("ideas_history.json", "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open("ideas_history.json", "w") as f:
        json.dump(history, f, indent=4)

def encode_kroki(mermaid_txt):
    """Encodes mermaid text into a Kroki-compatible base64 format."""
    compressed = zlib.compress(mermaid_txt.encode('utf-8'), 9)
    return base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')

def generate_idea(existing_ideas):
    all_past_keywords = []
    for idea in existing_ideas:
        keys = idea.get('keywords', [])
        if isinstance(keys, list):
            all_past_keywords.extend(keys)
    all_past_keywords = list(set(all_past_keywords))

    prompt = f"""
You are an intelligent but extremely practical SaaS founder who explains things so simply that even a beginner can understand, but you explain them in EXTREME DETAIL.

Generate ONE highly unique, lucrative, B2B or B2C micro-SaaS idea. 
It must be easy to visualize, solve a clear everyday problem, and be executable by a small team in 30 days.

Constraints:
- NEVER repeat these existing software names: {json.dumps([idea.get('idea_name', '') for idea in existing_ideas if idea.get('idea_name')])}
- NEVER repeat these topics/niches: {json.dumps([idea.get('topic', '') for idea in existing_ideas if idea.get('topic')])}
- NEVER reuse these core keywords/concepts: {json.dumps(all_past_keywords)}
- Make sure your new idea is from a COMPLETELY DIFFERENT topic/industry from the above.
- The `mermaid_architecture` field MUST contain a valid, clean Mermaid.js graph direction (e.g. graph TD) demonstrating the system's architecture (User -> Frontend -> Backend -> DB/AI).
- In the `system_architecture_deep_dive` field, provide an EXTREME, MASTERCLASS-LEVEL breakdown. Imagine you are writing for a total beginner who has never built a SaaS before. You must provide:
    1) THE ENGINE: List every single specific library, framework, and API required (e.g., 'Use React for UI, Tailwind for styling, Supabase for Auth/DB'). Explain WHY each is used.
    2) DATA HIGHWAY: Explain exactly how data moves from the user's click to the database. Describe what happens in the background step-by-step.
    3) INITIAL PROTOCOL: Tell them the exact first 5 steps they should take to start coding this (e.g., 'Step 1: Run npx create-react-app. Step 2: Install X. Step 3: Setup Y account').
    4) THE SECRET SAUCE: Mention one clever technical trick or logic they should implement to make the app better than competitors.
- CRITICAL: Use very simple language but provide MASSIVE amounts of text. No coding jargon without explaining it. This section should be long and extremely helpful.

OUTPUT STRICT JSON ONLY:
{{
  "date": "<YYYY-MM-DD>",
  "idea_name": "Catchy Name",
  "topic": "The core topic or niche (e.g., HR Tech, AI Legal Tool, Web3 Social)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "tagline": "A powerful, visionary tagline.",
  "the_problem_story": "Write a massive, deep story (4-5 sentences) describing the exact pain point. Make the reader FEEL the frustration. Details matter.",
  "the_solution_vision": "Explain in detail exactly how your tech swoops in like magic to solve it step-by-step. Break down what it actually does. (4-5 sentences)",
  "detailed_user_journey": "From start to finish: Step 1) User lands on page. Step 2) They upload X. Step 3) System processes Y. Step 4) Outcome is Z. Be extremely descriptive.",
  "mermaid_architecture": "graph TD\\n  User-->FrontEnd\\n  FrontEnd-->Backend\\n  Backend-->AI\\n  Backend-->DB",
  "system_architecture_deep_dive": "Extreme, long-form masterclass detail (400-600 words) for a beginner. Cover everything from setup commands to technical logic and secret tricks.",
  "target_audience": ["Person 1: Simple deep detail", "Person 2: Simple deep detail"],
  "financials": {{
    "model": "Subscription, pay-per-use, or hybrid model explained simply.",
    "tiers": [
      "Tier 1: <Name> - <Price> - Deep description of why this price point works for small users.",
      "Tier 2: <Name> - <Price> - Deep description of why this is the most popular/profitable choice.",
      "Tier 3: <Name> - <Price> - High-ticket details for enterprise/power users."
    ],
    "arr_potential": "A realistic, calculated $ value (e.g. $12,500/mo * 12 = $150k). Explain the logic/math behind this number.",
    "monetization_masterplan": "A massive, step-by-step 'Money Masterclass' (400-600 words) for a total beginner. You MUST include: 1) SETUP: Exactly which payment gateway to use (Stripe/LemonSqueezy) and the first 3 steps to go live. 2) PSYCHOLOGY: Why these specific prices will make users say 'Take my money!' 3) GROWTH HACKS: One specific trick to double the revenue (e.g., 'The Middle-Price Trap' or 'Annual Discount'). 4) CHURN SHIELD: One specific way to stop users from canceling. Make it so detailed that a beginner doesn't need to Google anything."
  }},
  "tech_stack": ["Tech 1", "Tech 2", "Tech 3", "Tech 4"],
  "go_to_market": ["Detailed Step 1 to get users", "Detailed Step 2 to get users"],
  "execution_timeline": ["Week 1: Exact daily details", "Week 2: Exact daily details", "Week 3: Exact daily details", "Week 4: Launch details"]
}}
"""

    model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})
    
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise e
        
    try:
        text = response.text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
            
        idea = json.loads(text)
        idea['date'] = datetime.now().strftime("%Y-%m-%d")
        return idea
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print("Raw response:", getattr(response, 'text', 'No text in response'))
        raise e

def create_html_email(idea):
    # Process mermaid graph to image
    mermaid_code = idea.get('mermaid_architecture', 'graph TD\\nA-->B')
    kroki_encoded = encode_kroki(mermaid_code)
    # We use PNG because many email clients block SVG from rendering
    diagram_url = f"https://kroki.io/mermaid/png/{kroki_encoded}"
    
    # Pre-build list HTML strings
    audience_list = ''.join([f'<li style="margin-bottom: 8px;"><strong>🎯 </strong> {aud}</li>' for aud in idea.get('target_audience', [])])
    pricing_list = ''.join([f'<li style="margin-bottom: 8px;"><strong>💸 </strong> {tier}</li>' for tier in idea.get('financials', {}).get('tiers', [])])
    tech_list = ''.join([f'<span style="display:inline-block; margin:4px; padding:6px 12px; background:#f1f5f9; border-radius:20px; font-size:13px; color:#334155; font-weight:600; border:1px solid #e2e8f0;">{tech}</span>' for tech in idea.get('tech_stack', [])])
    gtm_list = ''.join([f'<li style="margin-bottom: 8px;"><strong>🚀 </strong> {step}</li>' for step in idea.get('go_to_market', [])])
    execution_list = ''.join([f'<li style="margin-bottom: 12px; padding: 10px; background:#f8fafc; border-left:4px solid #3b82f6; border-radius:4px;">⏱️ {step}</li>' for step in idea.get('execution_timeline', [])])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                margin: 0; padding: 30px 15px; background-color: #eef2f6; color: #1e293b;
            }}
            .email-container {{
                max-width: 650px; margin: 0 auto; background: #ffffff; 
                border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            }}
            .hero {{
                background-color: #1e1b4b;
                background-image: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
                color: #ffffff; padding: 50px 40px; text-align: center;
            }}
            .hero h1 {{
                margin: 0; font-size: 34px; font-weight: 800; letter-spacing: -1px;
                color: #ffffff;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .hero p {{
                margin-top: 15px; font-size: 18px; font-weight: 400; color: #94a3b8; line-height: 1.5;
            }}
            .content-wrapper {{ padding: 40px; }}
            .story-block {{
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; margin-bottom: 30px;
            }}
            .story-block h3 {{ margin-top: 0; color: #dc2626; font-size: 18px; display: flex; align-items: center; gap: 8px; }}
            .story-block .solution-title {{ color: #059669; }}
            .story-block p {{ color: #475569; line-height: 1.7; margin-bottom: 0; font-size: 15px; }}
            
            .section-header {{
                font-size: 20px; font-weight: 800; color: #0f172a; margin: 40px 0 20px 0;
                display: flex; align-items: center; gap: 10px;
            }}
            
            .diagram-container {{
                background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px;
                text-align: center; margin-bottom: 30px;
            }}
            .diagram-container img {{
                max-width: 100%; height: auto; border-radius: 8px;
            }}
            
            .data-grid {{
                display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;
            }}
            .data-card {{
                background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}
            .data-card h4 {{ margin: 0 0 15px 0; font-size: 16px; color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
            ul {{ padding-left: 0; list-style-type: none; margin: 0; }}
            
            .footer {{
                background: #f1f5f9; padding: 25px; text-align: center; font-size: 13px; color: #64748b;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Hero -->
            <div class="hero">
                <h1>{idea.get('idea_name', 'Next Big Thing')}</h1>
                <p>{idea.get('tagline', '')}</p>
            </div>
            
            <!-- Content -->
            <div class="content-wrapper">
                
                <div class="story-block" style="border-left: 4px solid #ef4444;">
                    <h3>🔥 The Severe Pain Point</h3>
                    <p>{idea.get('the_problem_story', '')}</p>
                </div>
                
                <div class="story-block" style="border-left: 4px solid #10b981;">
                    <h3 class="solution-title">✨ The Elegant Solution</h3>
                    <p>{idea.get('the_solution_vision', '')}</p>
                </div>

                <div class="section-header">🛤️ The Complete User Journey</div>
                <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; font-size: 15px; color: #475569; line-height: 1.7; margin-bottom: 30px;">
                    {idea.get('detailed_user_journey', '')}
                </div>

                <div class="section-header">🛠️ System Architecture</div>
                <div class="diagram-container">
                    <p style="margin-top:0; font-size:13px; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Data Flow & Tech Diagram</p>
                    <img src="{diagram_url}" alt="Architecture Diagram" />
                    <div style="margin-top: 15px;">
                        {tech_list}
                    </div>
                </div>
                
                <div class="section-header">🧬 The Technical Blueprint (Masterclass)</div>
                <div style="background: #fdfcfe; border: 1px solid #e9d5ff; border-left: 5px solid #a855f7; border-radius: 12px; padding: 30px; font-size: 16px; color: #3b0764; line-height: 1.8; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(168, 85, 247, 0.08); white-space: pre-line;">
                   {idea.get('system_architecture_deep_dive', 'Preparing technical blueprints...')}
                </div>

                <div class="data-grid">
                    <div class="data-card">
                        <h4>👥 Target Audience</h4>
                        <ul>{audience_list}</ul>
                    </div>
                    <div class="data-card" style="border-left: 4px solid #10b981;">
                        <h4>💎 Financial Potential</h4>
                        <p style="font-size: 13px; color: #64748b; margin-top:0;"><strong>Model:</strong> {idea.get('financials', {}).get('model', '')}</p>
                        <p style="font-size: 14px; color: #059669; font-weight:bold; background: #ecfdf5; padding: 10px; border-radius: 6px; margin: 10px 0;">🚀 {idea.get('financials', {}).get('arr_potential', '')}</p>
                        <ul style="font-size: 13px;">{pricing_list}</ul>
                    </div>
                </div>

                <div class="section-header">💰 The Money Masterclass (Profitable Execution)</div>
                <div style="background: #fffcf0; border: 1px solid #fef3c7; border-left: 5px solid #f59e0b; border-radius: 12px; padding: 30px; font-size: 16px; color: #78350f; line-height: 1.8; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.08); white-space: pre-line;">
                    {idea.get('financials', {}).get('monetization_masterplan', 'Developing monetization blueprints...')}
                </div>

                <div class="section-header">📈 Go-to-Market Strategy</div>
                <ul>{gtm_list}</ul>

                <div class="section-header">📅 30-Day Execution</div>
                <ul>{execution_list}</ul>

            </div>
            
            <!-- Footer -->
            <div class="footer">
                <strong>AI Intelligence</strong><br>
                Automated daily SaaS insight engine powered by Gemini AI & Kroki.<br>
                Keep innovating.
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(subject, html_content):
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = f"AI Business Ideas <{EMAIL_SENDER}>"
    
    recipients = [EMAIL_RECIPIENT]
    recipients = [r for r in recipients if r]
    
    msg['To'] = ", ".join(recipients)

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e

def main():
    print("Loading history...")
    history = load_history()
    
    print("Generating new idea...")
    new_idea = generate_idea(history)
    print(f"Generated Idea: {new_idea.get('idea_name')}")
    
    history.append({
        "id": str(uuid.uuid4()),
        "date": new_idea.get("date"),
        "idea_name": new_idea.get("idea_name"),
        "topic": new_idea.get("topic", "N/A"),
        "keywords": new_idea.get("keywords", [])
    })
    save_history(history)
    
    print("Sending email...")
    subject = f"Daily SaaS Idea: {new_idea.get('idea_name')} 🚀"
    html_content = create_html_email(new_idea)
    send_email(subject, html_content)
    print("Completed!")

if __name__ == "__main__":
    main()
