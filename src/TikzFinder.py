from collections import namedtuple
from functools import cached_property
from re import DOTALL, findall, finditer, search
import os
import re
import chardet

from TexSoup import TexSoup
from .demacro import TexDemacro, Error as DemacroError

from .ColoredLogger import ColoredLogger

class TikzFinder():
    """
    Find tikzpictures and associated captions in a latex document and extract
    them as minimal compileable documents. Uses a combination of regex (fast)
    and TexSoup (slow) for searching.
    """
    Tikz = namedtuple("TikZ", ['code', 'caption'])
    Preamble = namedtuple("Preamble", ['imports', 'macros'])

    def __init__(self, tex_file_path):
        self.logger = ColoredLogger().logger
        self.base_path = os.path.dirname(tex_file_path)
        self.merged_file = self._merge_tex_files(tex_file_path)
        self.tex = self._check(self._get_latex_content_from_file(self.merged_file))


    def _merge_tex_files(self, tex_file_path):
        output_file_path = os.path.splitext(tex_file_path)[0] + '_merged.tex'
        fout = open(output_file_path, 'w')
        # loop to megrge all the files
        self._parseinclude(tex_file_path, fout)
        return output_file_path

    def _parseinclude(self, includefile,outfh):
        if not os.path.isfile(includefile) or not os.access(includefile, os.R_OK):
            self.logger.error('Unable to open ' + includefile + ': does not exist or no read permissions')

        fincl = open(includefile, 'r')

        # parse file line by line
        for line in fincl:

            # strip out comments in the line, if any
            dc = line.split('\\%')       # look for escaped \%
            if (len(dc) == 1):           # then there is no \% to be escaped
                first_comm = dc[0].find('%')
                if (first_comm == -1):
                    decom = line
                else:
                    decom = line[:(first_comm+1)] + '\n'
            else: # we had to escape a \%
                decom = ""               # construct the uncommented part
                dc = line.split('%')
                for chunk in dc:  # look in each chunk to see if there is a %
                    if chunk and (chunk[-1] == '\\'):  # if % is escaped...
                        decom = decom + chunk + '%'
                    else:
                        if chunk and (chunk[-1] == '\n'):
                            decom = decom + chunk
                        else:
                            decom = decom + chunk + '%\n'
                        break


            #input_match = re.match(r'\s*\\input{(.+?)}', decom)
            #import_match = re.match(r'\s*\\import{(.+?)}{(.+?)}', decom)


            input_match = re.match(r'\s*\\input\{([^\}]+)\}', decom)
            import_match = re.match(r'\s*\\import\{([^\}]+)\}\{([^\}]+)\}', decom)



            if input_match:
                fname = input_match.group(1)
                if not fname.endswith('.tex'):
                    fname += '.tex'
                fullpath = os.path.join(self.base_path, fname)
                outfh.write('\n')

                #print('\tFound include for ' + fullpath + '\n')
                self._parseinclude(fullpath,outfh)

            elif import_match:
                directory, file = import_match.groups()
                if not file.endswith('.tex'):
                    file += '.tex'
                fullpath = os.path.join(self.base_path, directory, file)
                outfh.write('\n')

                #print('\tFound import for ' + fullpath + '\n')
                self._parseinclude(fullpath, outfh)

            else:
                outfh.write(decom)

        fincl.close()




    def _get_latex_content_from_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding']
            with open(file_path, 'r', encoding=encoding) as file:
                latex_content = file.read()
                return latex_content.strip()
        except Exception as e:
            self.logger.error(f'Error while opening {file_path}: {e}')
            return None


    def _check(self, tex):
        assert r"\documentclass" in tex, "No documentclass found!"
        assert r"\begin{document}" in tex, "No document found!"
        assert r"\end{document}" in tex, "File seems to be incomplete!"
        return tex

    @cached_property
    def _preamble(self) -> "Preamble":
        """
        Extract relevant package imports and possible macros from the document preamble.
        """
        # Patterns for the most common stuff to retain in a (tikz) document (\usepackage, \usetikzlibrary, \tikzset, etc).
        include = ["documentclass", "tikz", "tkz", "pgf", "marvosym"]
        # Patterns for other commonly used packages
        packages = ["inputenc", "fontenc", "fontspec", "amsmath", "amssymb", "color"]
        # hard exclude macros ([re]newcommand, [re]newenvironment), as they are handled by de-macro
        exclude = [r"\new", r"\renew"]
        preamble, *_ = self.tex.partition(r"\begin{document}")

        try:
            # try TexSoup first, as it works with multiline statements
            soup = TexSoup(preamble, tolerance=1)
            statements = map(str, soup.children)
        except:
            statements = preamble.split("\n")

        tikz_preamble, maybe_macros = list(), list()
        for stmt in statements:
            if not stmt.lstrip().startswith("%"): # filter line comments
                if not any(stmt.lstrip().startswith(pat) for pat in exclude) and (
                    any(pat in stmt for pat in include) or (
                    stmt.lstrip().startswith(r"\usepackage") and any(pat in stmt for pat in packages)
                )):
                    tikz_preamble.append(stmt)
                else:
                    maybe_macros.append(stmt)

        return self.Preamble(imports="\n".join(tikz_preamble).strip(), macros="\n".join(maybe_macros).strip())

    def _process_macros(self, macros, tikz, expand=True):
        try:
            ts = TexDemacro(macros=macros)
            return ts.process(tikz) if expand else "\n\n".join(ts.find(tikz)).strip()
        except (DemacroError, RecursionError, TypeError):
            return tikz if expand else ""



    def _find_colorlets(self, macros, tikz):
        colorlet_regrex = colorlet_regex = r'\\colorlet\{(\w+?)\}\{(\w+?)\}'
        matches = list()
        for color in finditer(colorlet_regex, macros, re.MULTILINE):
            name, definition = color.group(1), color.group().lstrip()
            if search(rf"\b{name}\b", tikz):
                matches.append(definition)
        return "\n".join(matches).strip()


    def _find_colordefs(self, macros, tikz):
        definecolor_regex = r'^\s*\\definecolor(?:\[\w+?\])?\{(\w+?)\}\{\w+?\}\{.+?\}'

        matches = list()
        for color in finditer(definecolor_regex, macros, re.MULTILINE):
            name, definition = color.group(1), color.group().lstrip()
            if search(rf"\b{name}\b", tikz):
                matches.append(definition)
        return "\n".join(matches).strip()


    def _make_document(self, tikz: str) -> str:
        # if the tikzpicture uses some macros, append them to the tikz preamble
        macros = self._process_macros(self._preamble.macros, tikz, expand=False)

        # also search for utilized color definitions and colorlets
        colorlet = self._find_colorlets(self._preamble.macros, tikz)
        definecolor = self._find_colordefs(self._preamble.macros, colorlet+"\n"+tikz)
        extended_preamble = self._preamble.imports + (f"\n\n{definecolor}" if definecolor else "")  + (f"\n{colorlet}" if colorlet else "") + (f"\n\n{macros}" if macros else "")

        return "\n\n".join([extended_preamble, r"\begin{document}", tikz, r"\end{document}"])


    def _clean_caption(self, caption: str) -> str:
        # expand any macros
        caption = self._process_macros(self._preamble.macros, caption)

        try:
            cap_soup = TexSoup(caption, tolerance=1)
            # remove any labels
            for label in cap_soup.find_all("label"):
                label.delete() # type: ignore
            caption = str(cap_soup)
        except:
            pass

        return " ".join(caption.split())

    def _find_caption(self, figure: str) -> str:
        """
        Captions need special handling, since we can't express balanced
        parentheses in regex.
        """
        (*_, raw_caption), caption, unmatched_parens = figure.partition(r"\caption{"), "", 1

        for c in raw_caption:
            if c == '}':
                unmatched_parens -= 1
            elif c == '{':
                unmatched_parens += 1
            if not unmatched_parens:
                break
            caption += c

        return caption

    def find(self):
        for figure in findall(r"\\begin{figure\*?}(.*?)\\end{figure\*?}", self.tex, DOTALL):
            if figure.count(r"\begin{tikzpicture}") == 1: # multiple tikzpictures (e.g. subfig) are above my paygrade
                if tikz := search(r"(\\begin{tikzpicture}.*\\end{tikzpicture})", figure, DOTALL):
                    if caption := self._find_caption(figure):
                        yield self.Tikz(self._make_document(tikz.group(1)), self._clean_caption(caption))

    def __call__(self, *args, **kwargs):
        yield from self.find(*args, **kwargs)
