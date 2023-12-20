import requests
import feedparser
import json
import os
import concurrent.futures
from src.ArxivCollector import ArxivCollector
from src.LatexProcessor import LatexProcessor

class ArxivAPI:
    def __init__(self, dir, subject, keyword):

        self.dir = dir
        self.keyword = keyword
        self.query = subject
        self.subject = subject.replace(".", "_")
        self.subject_path = os.path.join(self.dir, self.subject)
        self.json_file = os.path.join(self.subject_path, f"{self.subject}.json")
        self.fit_file = os.path.join(
            self.subject_path, f"{self.subject}_{self.keyword}_fit.json"
        )
        self.jsonl_file = os.path.join(self.subject_path, f"{self.subject}.jsonl")
        self.max_results = 40
        self.start = 0
        self.sorting_method = "submittedDate"
        self.order = "descending"
        self.on_init()

    def on_init(self):

        #self.setup_subject_directories()

        #self.get_list()

        self.collect = ArxivCollector(self)

        self.latex_processor = LatexProcessor(self)



    def setup_subject_directories(self):
        os.makedirs(self.subject_path, exist_ok=True)

    def destroy_subject_directories(self):
        shutil.rmtree(os.path.join(self.dir, self.subject))

    def get_list(self):
        start = self.start
        max_results = self.max_results
        sorting_method = self.sorting_method
        order = self.order
        paper_ids = []
        while max_results > 0:
            current_range = min(max_results, 40)
            paper_ids += self.search_query(
                self.query, start, current_range, sorting_method, order
            )
            max_results -= current_range
            start += current_range
            self.logger.info(f"{self.subject} +1 ")

        with open(self.json_file, "w") as file:
            json.dump(paper_ids, file)
        (f"{self.subject} finished")

    @staticmethod
    def search_query(query, start, max_results, sorting_method, order):
        query_terms = "query?search_query=all:" + query
        first_result = "&start=" + str(start)
        last_result = "&max_results=" + str(max_results)
        sort_parameter = "&sortBy=" + sorting_method
        sort_order = "&sortOrder=" + order
        results = feedparser.parse(
            "http://export.arxiv.org/api/"
            + query_terms
            + first_result
            + last_result
            + sort_parameter
            + sort_order
        )

        if results["status"] != 200:
            self.logger.error(f"HTTP Error {results['status']} in query")
            raise Exception("HTTP Error " + str(results["status"]) + " in query")
        return [entry["id"].split("/")[-1] for entry in results["entries"]]


def process_subject(subject, dir, keyword):
    api = ArxivAPI(dir=dir, subject=subject, keyword=keyword)
    # 这里可以调用 api.collect 等其他方法执行任务


if __name__ == "__main__":
    dir = "dataset"
    keyword = "tikzpicture"
    subjects=["astro-ph","cond-mat.dis-nn","cond-mat.mtrl-sci","cond-mat.other","cond-mat.quant-gas","cond-mat.soft","cond-mat.stat-mech","cond-mat.str-el","cond-mat.supr-con","cs.AI","cs.AR","cs.CC","cs.CE","cs.CG","cs.CL","cs.CR","cs.CV","cs.CY","cs.DB","cs.DC","cs.DL","cs.DM","cs.DS","cs.ET","cs.FL","cs.GL","cs.GR","cs.GT","cs.HC","cs.IR","cs.IT","cs.LG","cs.LO","cs.MA","cs.MM","cs.MS","cs.NA","cs.NE","cs.NI","cs.OH","cs.OS","cs.PF","cs.PL","cs.RO","cs.SC","cs.SD","cs.SE","cs.SI","cs.SY","gr-qc","hep-ex","hep-lat","hep-ph","hep-th","math.AC","math.AG","math.AP","math.AT","math.CA","math.CO","math.CT","math.CV","math.DG","math.DS","math.FA","math.GM","math.GN","math.GR","math.GT","math.HO","math.IT","math.KT","math.LO","math.MG","math.MP","math.NA","math.NT","math.OA","math.OC","math.PR","math.QA","math.RA","math.RT","math.SG","math.SP","math.ST","math.ph","nlin.AO","nlin.CD","nlin.CG","nlin.PS","nlin.SI","nucl-ex","nucl-th","physics","physics.acc-ph","physics.ao-ph","physics.app-ph","physics.atm-clus","physics.atom-ph","physics.bio-ph","physics.chem-ph","physics.class-ph","physics.comp-ph","physics.data-an","physics.ed-ph","physics.flu-dyn","physics.gen-ph","physics.geo-ph","physics.hist-ph","physics.ins-det","physics.med-ph","physics.optics","physics.plasm-ph","physics.pop-ph","physics.soc-ph","physics.space-ph","q-bio.BM","q-bio.CB","q-bio.GN","q-bio.MN","q-bio.NC","q-bio.OT","q-bio.PE","q-bio.QM","q-bio.SC","q-bio.TO","q-fin.CP","q-fin.EC","q-fin.GN","q-fin.MF","q-fin.PM","q-fin.PR","q-fin.RM","q-fin.ST","q-fin.TR","quant-ph","stat.AP","stat.CO","stat.ME","stat.ML","stat.OT","stat.TH"]


    # subjects = ["q-fin.ST", "q-fin.PR", "physics.ed-ph", "q-bio.MN", "cs.MS", "q-bio.GN", "physics.geo-ph", "physics.hist-ph", "cs.SC", "q-bio.SC", "q-fin.CP", "math.GN", "nlin.CG", "q-fin.RM", "cs.FL", "q-fin.TR", "cs.DL", "q-fin.PM", "cs.AR", "cs.GL", "cs.PF", "q-fin.MF", "q-fin.GN", "q-bio.TO", "math.HO", "stat.OT", "math.GM", "q-fin.EC", "q-bio.OT", "q-bio.CB", "math.ph", "physics.pop-ph", "cs.OH", "cs.ET", "cs.OS", "physics.atm-clus"]
    # subjects= ['q-fin.ST','q-fin.PR','physics.ed-ph','q-bio.MN','cs.MS','q-bio.GN','physics.geo-ph','physics.hist-ph','cs.SC','q-bio.SC','q-fin.CP','math.GN','nlin.CG','q-fin.RM','cs.FL','q-fin.TR','cs.DL','q-fin.PM','cs.AR','cs.GL','cs.PF','q-fin.MF','q-fin.GN','q-bio.TO','math.HO','stat.OT','math.GM','q-fin.EC','q-bio.OT','q-bio.CB','math.ph','physics.pop-ph','cs.OH','cs.ET','cs.OS','physics.atm-clus']
    #    subjects = ['cond-mat.str-el', 'q-fin.ST', 'cs.NA', 'q-fin.PR', 'q-bio.MN', 'q-bio.BM', 'nucl-th', 'hep-ex', 'q-bio.GN', 'cs.SD', 'cs.SC', 'physics.comp-ph', 'cs.SY', 'q-bio.PE', 'stat.AP', 'gr-qc', 'cs.SE', 'q-bio.SC', 'cs.RO', 'q-fin.CP', 'stat.CO', 'math.SP', 'q-fin.RM', 'q-fin.TR', 'physics.space-ph', 'astro-ph', 'cs.IR', 'q-fin.PM', 'q-bio.NC', 'cs.AR', 'hep-th', 'cs.SI', 'stat.ML', 'stat.ME', 'q-fin.MF', 'nucl-ex', 'q-fin.GN', 'q-bio.TO', 'stat.OT', 'physics', 'hep-ph', 'q-bio.QM', 'q-fin.EC', 'stat.TH', 'q-bio.OT', 'q-bio.CB', 'math.ph', 'cs.OS', 'hep-lat', 'cs.CV']
    # subjects = ['cond-mat.dis-nn', 'cond-mat.mtrl-sci', 'cond-mat.mtrl-sci', 'cond-mat.other', 'cond-mat.quant-gas', 'cond-mat.soft', 'cond-mat.stat-mech', 'cond-mat.str-el', 'cond-mat.supr-con', 'physics.acc-ph', 'physics.app-ph', 'physics.ao-ph', 'physics.atom-ph', 'physics.atm-clus', 'physics.bio-ph', 'physics.chem-ph', 'physics.class-ph', 'physics.comp-ph', 'physics.data-an', 'physics.flu-dyn', 'physics.gen-ph', 'physics.geo-ph', 'physics.hist-ph', 'physics.ins-det', 'physics.med-ph', 'physics.optics', 'physics.ed-ph', 'physics.soc-ph', 'physics.plasm-ph', 'physics.pop-ph', 'physics.space-ph', 'math.AG','math.AT', 'math.AP', 'math.CA', 'math.CT', 'math.CO', 'math.AC',  'math.CV', 'math.DG', 'math.DS', 'math.FA', 'math.GM', 'math.GN', 'math.GT', 'math.GR', 'math.HO', 'math.IT', 'math.KT', 'math.LO', 'math.MP', 'math.MG', 'math.NT', 'math.NA', 'math.OA', 'math.OC', 'math.PR', 'math.QA', 'math.RT', 'math.RA', 'math.SP', 'math.ST', 'math.SG', 'quant-ph', 'nlin.AO', 'nlin.CG', 'nlin.CD', 'nlin.SI','nlin.PS', 'cs.AI', 'cs.CC', 'cs.CG', 'cs.CE', 'cs.CL', 'cs.CV', 'cs.CY', 'cs.CR', 'cs.DB', 'cs.DS', 'cs.DL', 'cs.DM', 'cs.DC', 'cs.ET', 'cs.FL', 'cs.GT', 'cs.GL',	'cs.GR', 'cs.AR', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MS', 'cs.MA', 'cs.MM', 'cs.NI', 'cs.NE', 'cs.NA', 'cs.OS', 'cs.OH', 'cs.PF', 'cs.PL', 'cs.RO','cs.SI', 'cs.SE', 'cs.SD', 'cs.SC', 'cs.SY', 'q-bio.BM', 'q-bio.CB', 'q-bio.GN', 'q-bio.MN', 'q-bio.NC', 'q-bio.OT', 'q-bio.PE', 'q-bio.QM', 'q-bio.SC', 'q-bio.TO','q-fin.CP', 'q-fin.EC', 'q-fin.GN', 'q-fin.MF', 'q-fin.PM', 'q-fin.PR', 'q-fin.RM', 'q-fin.ST', 'q-fin.TR', 'stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.OT', 'stat.TH', 'astro-ph', 'gr-qc', 'hep-ex', 'hep-lat', 'hep-ph', 'hep-th', 'math.ph', 'nucl-ex', 'nucl-th', 'physics']

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_subject, subject, dir, keyword)
            for subject in subjects
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # 如果需要，可以处理返回结果或异常
