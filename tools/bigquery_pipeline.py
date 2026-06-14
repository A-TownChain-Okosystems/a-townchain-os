"""
tools/bigquery_pipeline.py — A-TownChain BigQuery Analytics (Issue #49, Kap. 60)
Dataset: kai_os_analytics | 8 Tabellen | Streaming-Insert + täglicher Sync
Setup: export GCP_PROJECT_ID=... && export GOOGLE_APPLICATION_CREDENTIALS=...
"""
import datetime,json,logging,os
from typing import Dict,List,Optional

logger=logging.getLogger("tools.bigquery")
GCP_PROJECT_ID=os.environ.get("GCP_PROJECT_ID","atcchain-analytics")
DATASET_ID="kai_os_analytics"

SCHEMAS:Dict[str,List[dict]]={
    "blocks":[{"name":"block_number","type":"INTEGER","mode":"REQUIRED"},{"name":"block_hash","type":"STRING","mode":"REQUIRED"},{"name":"timestamp","type":"TIMESTAMP","mode":"REQUIRED"},{"name":"tx_count","type":"INTEGER","mode":"REQUIRED"},{"name":"gas_used","type":"INTEGER","mode":"NULLABLE"},{"name":"chain_id","type":"INTEGER","mode":"REQUIRED"}],
    "transactions":[{"name":"tx_hash","type":"STRING","mode":"REQUIRED"},{"name":"block_number","type":"INTEGER","mode":"REQUIRED"},{"name":"from_address","type":"STRING","mode":"REQUIRED"},{"name":"to_address","type":"STRING","mode":"NULLABLE"},{"name":"value_atc","type":"FLOAT","mode":"REQUIRED"},{"name":"status","type":"STRING","mode":"REQUIRED"},{"name":"timestamp","type":"TIMESTAMP","mode":"REQUIRED"}],
    "agents":[{"name":"agent_id","type":"STRING","mode":"REQUIRED"},{"name":"agent_type","type":"STRING","mode":"REQUIRED"},{"name":"model","type":"STRING","mode":"NULLABLE"},{"name":"requests_count","type":"INTEGER","mode":"REQUIRED"},{"name":"latency_ms_avg","type":"FLOAT","mode":"NULLABLE"},{"name":"date","type":"DATE","mode":"REQUIRED"}],
    "votes":[{"name":"proposal_id","type":"STRING","mode":"REQUIRED"},{"name":"voter","type":"STRING","mode":"REQUIRED"},{"name":"vote","type":"STRING","mode":"REQUIRED"},{"name":"weight","type":"FLOAT","mode":"REQUIRED"},{"name":"timestamp","type":"TIMESTAMP","mode":"REQUIRED"}],
    "nft_events":[{"name":"event_type","type":"STRING","mode":"REQUIRED"},{"name":"token_id","type":"STRING","mode":"REQUIRED"},{"name":"to_address","type":"STRING","mode":"REQUIRED"},{"name":"price_atc","type":"FLOAT","mode":"NULLABLE"},{"name":"timestamp","type":"TIMESTAMP","mode":"REQUIRED"}],
    "dex_swaps":[{"name":"tx_hash","type":"STRING","mode":"REQUIRED"},{"name":"pool","type":"STRING","mode":"REQUIRED"},{"name":"token_in","type":"STRING","mode":"REQUIRED"},{"name":"amount_in","type":"FLOAT","mode":"REQUIRED"},{"name":"amount_out","type":"FLOAT","mode":"REQUIRED"},{"name":"fee_bps","type":"INTEGER","mode":"REQUIRED"},{"name":"timestamp","type":"TIMESTAMP","mode":"REQUIRED"}],
    "wiki_chapters":[{"name":"chapter_id","type":"INTEGER","mode":"REQUIRED"},{"name":"title","type":"STRING","mode":"REQUIRED"},{"name":"word_count","type":"INTEGER","mode":"NULLABLE"},{"name":"last_updated","type":"DATE","mode":"REQUIRED"},{"name":"status","type":"STRING","mode":"REQUIRED"},{"name":"completeness_pct","type":"FLOAT","mode":"NULLABLE"}],
    "github_metrics":[{"name":"date","type":"DATE","mode":"REQUIRED"},{"name":"repo","type":"STRING","mode":"REQUIRED"},{"name":"commits","type":"INTEGER","mode":"REQUIRED"},{"name":"open_issues","type":"INTEGER","mode":"REQUIRED"},{"name":"closed_issues","type":"INTEGER","mode":"REQUIRED"},{"name":"clones","type":"INTEGER","mode":"NULLABLE"},{"name":"unique_clones","type":"INTEGER","mode":"NULLABLE"}],
}

class BigQueryPipeline:
    def __init__(self,project=GCP_PROJECT_ID,dataset=DATASET_ID):
        self.project=project; self.dataset=dataset; self._client=None
        self._dry=not bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
        if self._dry: logger.warning("BQ DRY RUN — set GOOGLE_APPLICATION_CREDENTIALS")
        else: self._init()
    def _init(self):
        try:
            from google.cloud import bigquery
            self._client=bigquery.Client(project=self.project)
            logger.info(f"BigQuery: {self.project}.{self.dataset}")
        except ImportError: logger.error("pip install google-cloud-bigquery"); self._dry=True
    def setup_dataset(self)->bool:
        if self._dry:
            logger.info(f"[DRY] Dataset: {self.project}.{self.dataset}")
            for t in SCHEMAS: logger.info(f"[DRY] Table: {t}")
            return True
        from google.cloud import bigquery,exceptions
        ref=f"{self.project}.{self.dataset}"
        try: self._client.get_dataset(ref)
        except exceptions.NotFound:
            ds=bigquery.Dataset(ref); ds.location="EU"
            ds.description="A-TownChain OS Analytics"
            self._client.create_dataset(ds); logger.info(f"Dataset created: {ref}")
        for tid,fields in SCHEMAS.items():
            tref=f"{ref}.{tid}"
            try: self._client.get_table(tref)
            except exceptions.NotFound:
                from google.cloud.bigquery import SchemaField,Table
                schema=[SchemaField(f["name"],f["type"],mode=f.get("mode","NULLABLE")) for f in fields]
                self._client.create_table(Table(tref,schema=schema))
                logger.info(f"  Table: {tid}")
        return True
    def insert_rows(self,table:str,rows:List[dict])->bool:
        if not rows: return True
        if self._dry: logger.info(f"[DRY] {len(rows)} rows → {table}"); return True
        errs=self._client.insert_rows_json(f"{self.project}.{self.dataset}.{table}",rows)
        return not errs
    def insert_github_metrics(self,repo,commits,open_i,closed_i,clones=0,unique=0)->bool:
        return self.insert_rows("github_metrics",[{"date":datetime.date.today().isoformat(),"repo":repo,"commits":commits,"open_issues":open_i,"closed_issues":closed_i,"clones":clones,"unique_clones":unique}])
    def daily_sync(self,github_data:dict=None)->dict:
        results={}
        if github_data:
            for repo,m in github_data.items():
                results[repo]=self.insert_github_metrics(repo,m.get("commits",0),m.get("open_issues",0),m.get("closed_issues",0),m.get("clones",0),m.get("unique_clones",0))
        return {"date":datetime.date.today().isoformat(),"results":results,"dry_run":self._dry}
    def status(self)->dict:
        return {"project":self.project,"dataset":self.dataset,"tables":list(SCHEMAS.keys()),"dry_run":self._dry,"setup":"python3 tools/bigquery_pipeline.py --setup"}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description="A-TownChain BigQuery Pipeline")
    p.add_argument("--setup",action="store_true"); p.add_argument("--daily-sync",action="store_true")
    p.add_argument("--status",action="store_true"); p.add_argument("--project",default=GCP_PROJECT_ID)
    args=p.parse_args()
    pipeline=BigQueryPipeline(project=args.project)
    if args.setup:
        ok=pipeline.setup_dataset()
        print(f"{'OK' if ok else 'FAIL'} Dataset {pipeline.project}.{pipeline.dataset}")
        for t in SCHEMAS: print(f"  - {t} ({len(SCHEMAS[t])} cols)")
    elif args.daily_sync: print(json.dumps(pipeline.daily_sync(),indent=2))
    elif args.status: print(json.dumps(pipeline.status(),indent=2))
    else:
        print("Usage: --setup | --daily-sync | --status")
        print(f"  export GCP_PROJECT_ID=your-project")
        print(f"  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
