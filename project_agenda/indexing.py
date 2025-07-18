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

class ProjectAgendaIndexer:
    def __init__(self, mysql_config, es_host='http://localhost:9200'):
        """Initialize the indexer with database and Elasticsearch connections"""
        self.mysql_config = mysql_config
        self.es = Elasticsearch([es_host])
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index_name = 'project_agendas'
        self.batch_size = 50
        
    def parse_json_field(self, json_string, default=None):
        """Safely parse JSON fields from database"""
        if not json_string:
            return default if default is not None else []
        try:
            return json.loads(json_string) if isinstance(json_string, str) else json_string
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {json_string[:100]}...")
            return default if default is not None else []
    
    def fetch_projects(self, cursor, offset, limit):
        """Fetch projects with their agenda information"""
        query = """
        SELECT 
            p.id as project_id,
            p.topic,
            p.external_topic,
            p.client_id,
            p.client_name,
            p.client_geography,
            p.expert_geographies,
            p.account_manager,
            p.research_analysts,
            p.l0_domain,
            p.l1_domain,
            p.l2_domain,
            p.l3_domain,
            p.domain_others,
            p.functions,
            p.receiving_date,
            p.created_at,
            p.updated_at,
            p.case_code,
            p.target_date,
            p.priority,
            p.no_of_calls,
            p.call_count,
            p.total_revenue,
            p.target_companies,
            p.description,
            p.status,
            p.type,
            p.category,
            p.offlimit_topics,
            p.offlimit_companies,
            p.archetypes,
            p.applicable_agenda_id,
            a.id as agenda_id,
            a.questions as agenda_questions,
            a.title as agenda_title,
            a.description as agenda_description
        FROM projects p
        LEFT JOIN agendas a ON p.applicable_agenda_id = a.id
        WHERE p.status = 'Open'
        ORDER BY p.id
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, offset))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def fetch_expert_responses(self, cursor, project_id):
        """Fetch all expert responses for a project"""
        query = """
        SELECT 
            pea.id as pe_agenda_id,
            pea.fk_expert as expert_id,
            pea.status as agenda_status,
            pea.agenda_shared_on,
            pea.agenda_responded_on,
            pea.agenda_responses,
            pea.is_shared_with_client,
            pe.expert_name,
            pe.relevant_company,
            pe.relevant_designation,
            pe.relevant_division,
            pe.relevant_company_location,
            pe.expert_invitation,
            pe.state,
            e.headline as expert_headline,
            e.base_location as expert_location,
            e.functions as expert_functions,
            e.total_years_of_experience,
            CONCAT_WS(', ', e.domain_l0, e.domain_l1, e.domain_l2, e.domain_l3) as expert_domains
        FROM pe_agendas pea
        JOIN project_experts pe ON pea.fk_pe = pe.id
        JOIN experts e ON pea.fk_expert = e.id
        WHERE pea.fk_project = %s 
            AND pea.status = 'Responded'
            AND pea.is_deleted = 0
        """
        
        cursor.execute(query, (project_id,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def parse_agenda_questions(self, questions_json):
        """Parse agenda questions from JSON"""
        questions = self.parse_json_field(questions_json, [])
        
        parsed_questions = []
        for idx, q in enumerate(questions):
            if isinstance(q, dict):
                parsed_questions.append({
                    'question_id': str(q.get('id', idx)),
                    'question_text': q.get('question', q.get('text', '')),
                    'question_type': q.get('type', 'text'),
                    'required': q.get('required', False),
                    'order': q.get('order', idx)
                })
        
        return parsed_questions
    
    def parse_agenda_responses(self, responses_json, questions):
        """Parse expert responses and match with questions"""
        responses = self.parse_json_field(responses_json, {})
        
        parsed_responses = []
        for question in questions:
            q_id = question['question_id']
            
            # Try different possible keys for the answer
            answer = responses.get(q_id) or \
                    responses.get(f'question_{q_id}') or \
                    responses.get(str(q_id)) or ''
            
            if answer:
                parsed_responses.append({
                    'question_id': q_id,
                    'question_text': question['question_text'],
                    'answer': str(answer)
                })
        
        return parsed_responses
    
    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        if not texts or all(not t for t in texts):
            return [None] * len(texts)
        
        # Replace empty texts with space to avoid errors
        processed_texts = [t if t else " " for t in texts]
        embeddings = self.model.encode(processed_texts, normalize_embeddings=True)
        
        return [emb.tolist() if texts[i] else None for i, emb in enumerate(embeddings)]
    
    def process_project(self, project, cursor):
        """Process a single project and prepare it for indexing"""
        try:
            # Parse agenda questions
            questions = self.parse_agenda_questions(project.get('agenda_questions'))
            
            # Generate project-level text for embeddings
            project_desc_text = ' '.join(filter(None, [
                project.get('topic', ''),
                project.get('external_topic', ''),
                project.get('description', ''),
                project.get('target_companies', ''),
                project.get('archetypes', '')
            ]))
            
            questions_text = ' '.join([q['question_text'] for q in questions])
            
            combined_project_text = f"{project_desc_text} {questions_text}"
            
            # Fetch expert responses
            expert_responses = []
            if project.get('project_id'):
                db_responses = self.fetch_expert_responses(cursor, project['project_id'])
                
                for resp in db_responses:
                    # Parse individual responses
                    parsed_responses = self.parse_agenda_responses(
                        resp['agenda_responses'], 
                        questions
                    )
                    
                    if parsed_responses:
                        # Generate combined Q&A text
                        qa_texts = [f"{r['question_text']}: {r['answer']}" 
                                  for r in parsed_responses]
                        combined_qa_text = ' '.join(qa_texts)
                        
                        # Generate embeddings for answers
                        answer_texts = [r['answer'] for r in parsed_responses]
                        answer_embeddings = self.generate_embeddings(answer_texts)
                        
                        # Add embeddings to responses
                        for i, r in enumerate(parsed_responses):
                            r['answer_embedding'] = answer_embeddings[i]
                        
                        # Generate combined embedding
                        combined_qa_embedding = self.generate_embeddings([combined_qa_text])[0]
                        
                        expert_responses.append({
                            'pe_agenda_id': resp['pe_agenda_id'],
                            'expert_id': resp['expert_id'],
                            'expert_name': resp['expert_name'],
                            'expert_headline': resp.get('expert_headline'),
                            'expert_location': resp.get('expert_location'),
                            'expert_functions': resp.get('expert_functions'),
                            'expert_domains': resp.get('expert_domains'),
                            'years_of_experience': resp.get('total_years_of_experience'),
                            'relevant_company': resp.get('relevant_company'),
                            'relevant_designation': resp.get('relevant_designation'),
                            'relevant_division': resp.get('relevant_division'),
                            'agenda_status': resp.get('agenda_status'),
                            'expert_invitation': resp.get('expert_invitation'),
                            'state': resp.get('state'),
                            'shared_on': resp.get('agenda_shared_on'),
                            'responded_on': resp.get('agenda_responded_on'),
                            'responses': parsed_responses,
                            'combined_qa_text': combined_qa_text,
                            'combined_qa_embedding': combined_qa_embedding
                        })
            
            # Generate project-level embeddings
            embeddings = self.generate_embeddings([
                project_desc_text,
                questions_text,
                combined_project_text
            ])
            
            # Prepare final document
            document = {
                'project_id': project['project_id'],
                'topic': project.get('topic'),
                'external_topic': project.get('external_topic'),
                'client_id': project.get('client_id'),
                'client_name': project.get('client_name'),
                'client_geography': project.get('client_geography'),
                'expert_geographies': self.parse_json_field(project.get('expert_geographies'), []),
                'account_manager': project.get('account_manager'),
                'research_analysts': self.parse_json_field(project.get('research_analysts'), []),
                'case_code': self.parse_json_field(project.get('case_code'), []),
                'priority': project.get('priority'),
                'status': project.get('status'),
                'type': project.get('type'),
                'category': project.get('category'),
                'no_of_calls': project.get('no_of_calls'),
                'call_count': project.get('call_count'),
                'total_revenue': project.get('total_revenue'),
                'description': project.get('description'),
                'target_companies': project.get('target_companies'),
                'archetypes': project.get('archetypes'),
                'offlimit_topics': project.get('offlimit_topics'),
                'offlimit_companies': project.get('offlimit_companies'),
                'domains': {
                    'l0': project.get('l0_domain'),
                    'l1': project.get('l1_domain'),
                    'l2': project.get('l2_domain'),
                    'l3': project.get('l3_domain'),
                    'others': project.get('domain_others')
                },
                'functions': project.get('functions'),
                'receiving_date': project.get('receiving_date'),
                'created_at': project.get('created_at'),
                'updated_at': project.get('updated_at'),
                'target_date': project.get('target_date'),
                'applicable_agenda_id': project.get('applicable_agenda_id'),
                'agenda_questions': questions,
                'expert_responses': expert_responses,
                'project_description_embedding': embeddings[0],
                'agenda_questions_embedding': embeddings[1],
                'combined_project_embedding': embeddings[2]
            }
            
            # Clean up None values
            document = {k: v for k, v in document.items() if v is not None}
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing project {project.get('project_id')}: {str(e)}")
            return None
    
    def index_all_projects(self):
        """Main function to index all projects"""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM projects WHERE status = 'Open'")
            total = cursor.fetchone()['total']
            logger.info(f"Total projects to index: {total}")
            
            offset = 0
            indexed_count = 0
            
            with tqdm(total=total, desc="Indexing projects") as pbar:
                while offset < total:
                    # Fetch batch of projects
                    projects = self.fetch_projects(cursor, offset, self.batch_size)
                    
                    if not projects:
                        break
                    
                    # Process projects
                    documents = []
                    for project in projects:
                        doc = self.process_project(project, cursor)
                        if doc:
                            documents.append(doc)
                    
                    # Bulk index
                    if documents:
                        success_count = self.bulk_index_documents(documents)
                        indexed_count += success_count
                    
                    offset += self.batch_size
                    pbar.update(len(projects))
            
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
                "_id": f"project_{doc['project_id']}",
                "_source": doc
            })
        
        try:
            success, failed = bulk(self.es, actions, raise_on_error=False)
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents")
                for item in failed:
                    logger.error(f"Failed document: {item}")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing error: {str(e)}")
            return 0

if __name__ == "__main__":
    # MySQL configuration

    mysql_config = {
        'host': 'localhost',
        'user': 'username',
        'password': 'password',
        'database': 'database',
        'port': 3306
    }
    
    # Create and run indexer
    indexer = ProjectAgendaIndexer(mysql_config)
    
    # First create the index (if not already created)
    from create_index import create_project_agenda_index
    create_project_agenda_index()
    
    # Then index the data
    indexer.index_all_projects()
