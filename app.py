from flask import Flask, request, jsonify
import os
import json
import csv
from datetime import datetime
from test import LinkedInScraper

app = Flask(__name__)
scraper = LinkedInScraper()

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "LinkedIn Scraper API is running",
        "endpoints": {
            "GET /": "API information",
            "POST /api/search/people": "Search for people on LinkedIn",
            "POST /api/search/companies": "Search for companies on LinkedIn",
            "POST /api/search/name": "Search for a specific person or company by name",
            "POST /api/tag": "Tag a lead",
            "GET /api/leads": "Get all leads",
            "GET /api/leads/tags/:tag": "Get leads by tag",
            "GET /api/leads/categories/:category": "Get leads by category",
            "GET /api/report": "Get leads report"
        }
    })

@app.route('/api/search/name', methods=['POST'])
def search_by_name():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    name = data.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400
        
    entity_type = data.get('type', 'auto').lower()  # 'person', 'company', or 'auto'
    
    try:
        results = []
        
        # If entity_type is 'auto', try to determine if it's a person or company
        if entity_type == 'auto':
            # First try as a person
            person_results = scraper.search_people(
                keywords=name,
                limit=5,
                use_real_data=True
            )
            
            # Then try as a company
            company_results = scraper.search_companies(
                keywords=name,
                limit=5,
                use_real_data=True
            )
            
            # Combine results
            results = {
                "people": person_results,
                "companies": company_results
            }
            
        elif entity_type == 'person':
            # Search for a person
            results = scraper.search_people(
                keywords=name,
                limit=5,
                use_real_data=True
            )
            
        elif entity_type == 'company':
            # Search for a company
            results = scraper.search_companies(
                keywords=name,
                limit=5,
                use_real_data=True
            )
        
        return jsonify({
            "status": "success",
            "query": name,
            "type": entity_type,
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search/people', methods=['POST'])
def search_people():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    keywords = data.get('keywords')
    if not keywords:
        return jsonify({"status": "error", "message": "Keywords are required"}), 400
        
    location = data.get('location')
    industry = data.get('industry')
    limit = data.get('limit', 10)
    use_real_data = data.get('use_real_data', True)
    
    try:
        results = scraper.search_people(
            keywords=keywords,
            location=location,
            industry=industry,
            limit=limit,
            use_real_data=use_real_data
        )
        
        # Auto-tag based on job titles if specified
        if data.get('auto_tag', False):
            for person in results:
                headline = person.get('headline', '').lower()
                if 'manager' in headline:
                    scraper.tag_lead(person, 'decision_maker')
                if 'director' in headline or 'ceo' in headline:
                    scraper.tag_lead(person, 'executive')
                if 'marketing' in headline:
                    scraper.tag_lead(person, 'marketing_professional')
        
        return jsonify({
            "status": "success",
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search/companies', methods=['POST'])
def search_companies():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    keywords = data.get('keywords')
    if not keywords:
        return jsonify({"status": "error", "message": "Keywords are required"}), 400
        
    industry = data.get('industry')
    company_size = data.get('company_size')
    limit = data.get('limit', 10)
    use_real_data = data.get('use_real_data', True)
    
    try:
        results = scraper.search_companies(
            keywords=keywords,
            industry=industry,
            company_size=company_size,
            limit=limit,
            use_real_data=use_real_data
        )
        
        return jsonify({
            "status": "success",
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tag', methods=['POST'])
def tag_lead():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    lead = data.get('lead')
    tag = data.get('tag')
    
    if not lead or not tag:
        return jsonify({"status": "error", "message": "Lead and tag are required"}), 400
        
    try:
        updated_lead = scraper.tag_lead(lead, tag)
        return jsonify({
            "status": "success",
            "lead": updated_lead
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/leads', methods=['GET'])
def get_leads():
    try:
        return jsonify({
            "status": "success",
            "count": len(scraper.leads_database),
            "leads": scraper.leads_database
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/leads/tags/<tag>', methods=['GET'])
def get_leads_by_tag(tag):
    try:
        leads = scraper.get_leads_by_tag(tag)
        return jsonify({
            "status": "success",
            "tag": tag,
            "count": len(leads),
            "leads": leads
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/leads/categories/<category>', methods=['GET'])
def get_leads_by_category(category):
    try:
        leads = scraper.get_leads_by_category(category)
        return jsonify({
            "status": "success",
            "category": category,
            "count": len(leads),
            "leads": leads
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/report', methods=['GET'])
def get_report():
    try:
        # Generate report data
        report = {
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_leads": len(scraper.leads_database),
            "people_count": sum(1 for lead in scraper.leads_database if "tags" in lead),
            "company_count": sum(1 for lead in scraper.leads_database if "category" in lead),
            "tags": {tag: len(leads) for tag, leads in scraper.tagged_leads.items()},
            "categories": {category: len(leads) for category, leads in scraper.categorized_companies.items()},
            "people": [lead for lead in scraper.leads_database if "tags" in lead],
            "companies": [lead for lead in scraper.leads_database if "category" in lead]
        }
        
        return jsonify({
            "status": "success",
            "report": report
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_leads():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    filename = data.get('filename', 'leads.json')
    format = data.get('format', 'json')
    tag = data.get('tag')
    category = data.get('category')
    
    try:
        # Determine which leads to save
        if tag:
            leads = scraper.get_leads_by_tag(tag)
        elif category:
            leads = scraper.get_leads_by_category(category)
        else:
            leads = scraper.leads_database
            
        success = scraper.save_leads(leads, filename, format)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Saved {len(leads)} leads to {filename}",
                "count": len(leads)
            })
        else:
            return jsonify({"status": "error", "message": "Failed to save leads"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/load', methods=['POST'])
def load_leads():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    filename = data.get('filename')
    format = data.get('format', 'json')
    
    if not filename:
        return jsonify({"status": "error", "message": "Filename is required"}), 400
        
    try:
        leads = scraper.load_leads(filename, format)
        return jsonify({
            "status": "success",
            "message": f"Loaded {len(leads)} leads from {filename}",
            "count": len(leads),
            "leads": leads
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search/combined', methods=['POST'])
def search_combined():
    """Combined search for both people and companies"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    keywords = data.get('keywords')
    if not keywords:
        return jsonify({"status": "error", "message": "Keywords are required"}), 400
        
    location = data.get('location')
    industry = data.get('industry')
    limit = data.get('limit', 10)
    use_real_data = data.get('use_real_data', True)
    auto_tag = data.get('auto_tag', True)
    
    try:
        # Search for people
        people = scraper.search_people(
            keywords=keywords,
            location=location,
            industry=industry,
            limit=limit,
            use_real_data=use_real_data
        )
        
        # Search for companies
        companies = scraper.search_companies(
            keywords=keywords,
            industry=industry,
            limit=limit,
            use_real_data=use_real_data
        )
        
        # Auto-tag people if specified
        if auto_tag:
            for person in people:
                headline = person.get('headline', '').lower()
                if 'manager' in headline:
                    scraper.tag_lead(person, 'decision_maker')
                if 'director' in headline or 'ceo' in headline:
                    scraper.tag_lead(person, 'executive')
                if keywords.lower() in headline:
                    scraper.tag_lead(person, f"{keywords.lower()}_professional")
        
        # Save results to files
        all_leads = people + companies
        scraper.save_leads(all_leads, "all_leads.json")
        
        # Get decision makers
        decision_makers = scraper.get_leads_by_tag("decision_maker")
        if decision_makers:
            scraper.save_leads(decision_makers, "decision_makers.json")
        
        # Generate report
        scraper.export_leads_report(all_leads, "leads_report.txt")
        
        return jsonify({
            "status": "success",
            "people_count": len(people),
            "company_count": len(companies),
            "total_count": len(all_leads),
            "decision_makers_count": len(decision_makers) if 'decision_makers' in locals() else 0,
            "people": people,
            "companies": companies,
            "files_generated": [
                "all_leads.json",
                "decision_makers.json" if 'decision_makers' in locals() and decision_makers else None,
                "leads_report.txt"
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
