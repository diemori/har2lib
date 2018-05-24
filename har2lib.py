#-*- coding: utf-8 -*-

import sys
import json
from codecs import BOM_UTF8


def lstrip_bom(str_, bom=BOM_UTF8.decode('utf-8-sig')):
    if str_.startswith(bom):
        return str_[len(bom):]
    else:
        return str_


class HarLib:
    def __init__(self):
        self.file_name = ""
        self.tab_space = "    "
        self.exception_ext = ['html', 'js', 'css', 'gif', 'jpg', 'svg']

        pass

    def _load(self, file_path, har_enc='utf-8'):
        self.file_name = file_path.split('/')[-1]

        try:
            with open(file_path, 'r', encoding=har_enc) as fi:
                har_text = fi.read().replace(BOM_UTF8.decode('utf-8-sig'), "")

        except FileNotFoundError:
            return None

        return har_text

    def parse(self, file_path):
        print("[parse] %s" % file_path)

        har_text = self._load(file_path)

        if har_text is None:
            print("[parse][FileNotFoundError] %s" % file_path)
            return False

        har_json = json.loads(har_text)

        api_dict = {}

        creator = har_json["log"]["creator"]
        entries = har_json["log"]["entries"]

        for entry in entries:
            if self._check_exception(entry["request"]["url"]):
                continue

            function_param = {}

            for item in entry["request"]:
                if item == "url":
                    url = entry["request"][item]
                    function_param = self._get_url(url, function_param)

                if item == "headers":
                    function_param[item] = self._get_headers(entry["request"][item])

            function_param["method"] = '"' + entry["request"]["method"] + '"'

            api_dict[function_param["url_title"]] = function_param

        self._gen_py(api_dict, creator=creator)

    def _check_exception(self, url):
        for ext in self.exception_ext:
            if url.split('?')[0].endswith(ext):
                return True

        return False

    def _gen_py(self, api_dict, creator=""):
        ts = self.tab_space
        comment = "#-*- coding: utf-8 -*-\n" \
                  "# inwoo.ro\n" \
                  "# File Name: %s\n" \
                  "# Creator: %s\n\n" % (self.file_name, creator)

        with open(self.file_name.replace('.', '_').replace("_har", ".py"), 'w', encoding='utf-8') as fo:
            fo.write(comment)

            fo.write("import requests\n\n\n")

            for api_title in api_dict:
                func_name = api_title.replace('-', '')
                fo.write("def _%s():\n" % func_name)

                for name in api_dict[api_title]:
                    if name == 'url_title' or name == 'headers':
                        continue

                    fo.write(ts + name + ' = ' + api_dict[api_title][name] + '\n')

                fo.write(ts + "headers = " + api_dict[api_title]["headers"] + '\n')

                fo.write(ts + 'return True\n\n\n')

    # url 관련 정보 파싱하여 가져온다
    def _get_url(self, url, param):
        protocol = url.split(':')[0]

        # 도메인 부분에 포트 정보가 함께 있는 경우도 있고, 아닌 경우도 있다
        domain_port = url.replace(protocol + "://", "").split('/')[0]
        domain = domain_port
        port = ""

        if ':' in domain_port:
            domain = domain_port.split(':')[0]
            port = domain_port.split(':')[1]
        else:
            if protocol == "http":
                port = "80"
            else:
                port = "443"

        path = url.replace(protocol + "://" + domain_port, "")

        if '?' in path:
            arguments = path.split('?')[1].replace('&', '" \\\n%s"&' % (self.tab_space * 5))
            path = path.split('?')[0]
        else:
            arguments = ""

        title = path.split('/')[-1].split('.')[0]

        param["url"] = '"' + url + '"'
        param["url_protocol"] = '"' + protocol + '"'
        param["url_domain_port"] = '"' + domain_port + '"'
        param["url_domain"] = '"' + domain + '"'
        param["url_port"] = '"' + port + '"'
        param["url_path"] = '"' + path + '"'
        param["url_arguments"] = '"' + arguments + '"'
        param["url_title"] = title

        return param

    # 헤더 정보를 문자열로 파싱하여 저장한다
    def _get_headers(self, headers):
        result = "{\n"
        ts = self.tab_space

        for header in headers:
            header_str = ts * 2 + "'" + header['name'] + "': '" + header['value'] + "',\n"
            result += header_str

        result += ts + "}\n"

        return result


if __name__ == "__main__":
    hl = HarLib()
    file_name = sys.argv[1]

    hl.parse(file_name)
