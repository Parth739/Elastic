import mysql.connector
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertDataIndexer:
    def __init__(self, mysql_config, es_host='http://localhost:9200'):
        """Initialize the indexer with database and Elasticsearch connections"""
        self.mysql_config = mysql_config
        self.es = Elasticsearch([es_host])
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index_name = 'experts_data_index'
        self.batch_size = 100
        
    def parse_json_field(self, json_string, default=None):
        """Safely parse JSON fields from database"""
        if not json_string:
            return default if default is not None else []
        try:
            return json.loads(json_string) if isinstance(json_string, str) else json_string
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {json_string[:100]}...")
            return default if default is not None else []
    
    def fetch_experts(self, cursor, offset, limit):
        """Fetch experts from database"""
        query = """
        SELECT 
            e.*,
            GROUP_CONCAT(DISTINCT we.company) as companies_list,
            GROUP_CONCAT(DISTINCT we.designation) as designations_list
        FROM experts e
        LEFT JOIN work_experiences we ON e.id = we.expert_id
        GROUP BY e.id
        ORDER BY e.id
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, offset))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def fetch_work_experiences(self, cursor, expert_id):
        """Fetch work experiences for a specific expert"""
        query = """
        SELECT 
            id,
            company,
            fk_company,
            status,
            designation,
            division,
            job_description,
            country,
            location,
            start_date,
            end_date,
            currently_works_here
        FROM work_experiences
        WHERE expert_id = %s
        ORDER BY start_date DESC
        """
        
        cursor.execute(query, (expert_id,))
        columns = [desc[0] for desc in cursor.description]
        work_exps = []
        
        for row in cursor.fetchall():
            work_exp = dict(zip(columns, row))
            # Convert dates to string format
            if work_exp.get('start_date'):
                work_exp['start_date'] = work_exp['start_date'].strftime('%Y-%m-%d') if isinstance(work_exp['start_date'], datetime) else str(work_exp['start_date'])
            if work_exp.get('end_date'):
                work_exp['end_date'] = work_exp['end_date'].strftime('%Y-%m-%d') if isinstance(work_exp['end_date'], datetime) else str(work_exp['end_date'])
            work_exps.append(work_exp)
            
        return work_exps
    
    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        if not texts or all(not t for t in texts):
            return [None] * len(texts)
        
        # Replace empty texts with space to avoid errors
        processed_texts = [t if t else " " for t in texts]
        embeddings = self.model.encode(processed_texts, normalize_embeddings=True)
        
        return [emb.tolist() if texts[i] else None for i, emb in enumerate(embeddings)]
    
    def create_work_experience_text(self, work_experiences):
        """Create combined text from work experiences for embedding"""
        if not work_experiences:
            return ""
        
        work_exp_texts = []
        for we in work_experiences:
            # Combine relevant fields
            parts = []
            if we.get('designation'):
                parts.append(we['designation'])
            if we.get('company'):
                parts.append(f"at {we['company']}")
            if we.get('division'):
                parts.append(f"in {we['division']}")
            if we.get('job_description'):
                parts.append(we['job_description'])
            if we.get('location'):
                parts.append(f"based in {we['location']}")
                
            work_exp_texts.append(' '.join(parts))
        
        return ' | '.join(work_exp_texts)
    
    def process_expert(self, expert, cursor):
        """Process a single expert and prepare for indexing"""
        try:
            # Fetch work experiences
            work_experiences = self.fetch_work_experiences(cursor, expert['id'])
            
            # Generate text for embeddings
            bio_text = expert.get('bio', '') or ''
            headline_text = expert.get('headline', '') or ''
            work_exp_text = self.create_work_experience_text(work_experiences)
            
            # Combined text for overall embedding
            combined_text_parts = [
                expert.get('name', ''),
                headline_text,
                bio_text,
                work_exp_text,
                expert.get('functions', ''),
                expert.get('domain_l0', ''),
                expert.get('domain_l1', ''),
                expert.get('domain_l2', ''),
                expert.get('domain_l3', ''),
                expert.get('domain_other', '')
            ]
            combined_text = ' '.join(filter(None, combined_text_parts))
            
            # Generate embeddings
            embeddings = self.generate_embeddings([
                combined_text,
                bio_text,
                headline_text,
                work_exp_text
            ])
            
            # Prepare document
            document = {
                'id': expert['id'],
                'name': expert.get('name'),
                'type': expert.get('type'),
                'badge': expert.get('badge'),
                'source_link': expert.get('source_link'),
                'status': expert.get('status'),
                'private_profile': bool(expert.get('private_profile')),
                'dnd_enabled': bool(expert.get('dnd_enabled')),
                'premium_expert': bool(expert.get('premium_expert')),
                'base_location': expert.get('base_location'),
                'fk_project': expert.get('fk_project'),
                'is_self_registered': bool(expert.get('is_self_registered')),
                'user_id': expert.get('user_id'),
                'primary_mobile': expert.get('primary_mobile'),
                'all_mobile_numbers': expert.get('all_mobile_numbers'),
                'headline': headline_text,
                'functions': expert.get('functions'),
                'picture': expert.get('picture'),
                'bio': bio_text,
                'internal_notes': expert.get('internal_notes'),
                'expertise_in_these_geographies': expert.get('expertise_in_these_geographies'),
                'primary_email': expert.get('primary_email'),
                'all_emails': expert.get('all_emails'),
                'fk_creator': expert.get('fk_creator'),
                'updated_by': expert.get('updated_by'),
                'approved_by': expert.get('approved_by'),
                'domain_l0': expert.get('domain_l0'),
                'domain_l1': expert.get('domain_l1'),
                'domain_l2': expert.get('domain_l2'),
                'domain_l3': expert.get('domain_l3'),
                'domain_other': expert.get('domain_other'),
                'offlimit_topics': expert.get('offlimit_topics'),
                'offlimit_companies': expert.get('offlimit_companies'),
                'call_count': expert.get('call_count'),
                'pending_edits': expert.get('pending_edits'),
                'total_years_of_experience': expert.get('total_years_of_experience'),
                'work_experiences': work_experiences,  # Nested array
                'combined_embedding': embeddings[0],
                'bio_embedding': embeddings[1],
                'headline_embedding': embeddings[2],
                'work_experience_embedding': embeddings[3]
            }
            
            # Handle dates
            for date_field in ['created_at', 'updated_at', 'confirmed_on']:
                if expert.get(date_field):
                    if isinstance(expert[date_field], datetime):
                        document[date_field] = expert[date_field].strftime('%Y-%m-%d')
                    else:
                        document[date_field] = str(expert[date_field])
            
            # Parse JSON fields for awards, patents, etc.
            for json_field in ['awards', 'patents', 'snippets', 'education', 'webhandles', 'publications']:
                if expert.get(json_field):
                    document[json_field] = self.parse_json_field(expert[json_field], {})
            
            # Clean up None values
            document = {k: v for k, v in document.items() if v is not None}
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing expert {expert.get('id')}: {str(e)}")
            return None
    
    def index_all_experts(self):
        """Main function to index all experts"""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM experts")
            total = cursor.fetchone()['total']
            logger.info(f"Total experts to index: {total}")
            
            offset = 0
            indexed_count = 0
            
            with tqdm(total=total, desc="Indexing experts") as pbar:
                while offset < total:
                    # Fetch batch of experts
                    experts = self.fetch_experts(cursor, offset, self.batch_size)
                    
                    if not experts:
                        break
                    
                    # Process experts
                    documents = []
                    for expert in experts:
                        doc = self.process_expert(expert, cursor)
                        if doc:
                            documents.append(doc)
                    
                    # Bulk index
                    if documents:
                        success_count = self.bulk_index_documents(documents)
                        indexed_count += success_count
                    
                    offset += self.batch_size
                    pbar.update(len(experts))
            
            # Refresh index
            self.es.indices.refresh(index=self.index_name)
            logger.info(f"Indexing complete! Total documents indexed: {indexed_count}")
            
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def bulk_index_documents(self, documents):
        """Bulk index documents to Elasticsearch"""
        actions = []
        for doc in documents:
            actions.append({
                "_index": self.index_name,
                "_id": doc['id'],
                "_source": doc
            })
        
        try:
            success, failed = bulk(self.es, actions, raise_on_error=False, chunk_size=50)
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents")
                for item in failed:
                    logger.error(f"Failed document: {item}")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing error: {str(e)}")
            return 0

# Usage
if __name__ == "__main__":
    # MySQL configuration
    mysql_config = {
        'host': 'localhost',
        'user': 'your_username',
        'password': 'your_password',
        'database': 'your_database',
        'port': 3306
    }
    
    # First create the index using your existing function
    from create_index import create_expert_index
    create_expert_index()
    
    # Then index the data
    indexer = ExpertDataIndexer(mysql_config)
    indexer.index_all_experts()
