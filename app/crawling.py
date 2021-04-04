import json
import time

# import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

enzyme_class_list = []


def fetch_node_data(p_node):
    if '.-' in p_node['id']:
        i_url = f"https://www.uniprot.org/view/uniprot/by/ec/?format=json&query=reviewed:yes&parent={p_node['id']}"
        i_response = requests.get(i_url)
        i_nodes = json.loads(i_response.text)['nodes']

        for i_node in i_nodes:
            fetch_node_data(i_node)
    else:
        if 'n' in p_node['id']:
            return

        enzyme_class_list.append((p_node['id'], p_node['label']))


def crawling_enzyme_class_list():
    f = open('enzyme_class_list.tsv', 'w+')

    url = "https://www.uniprot.org/view/uniprot/by/ec/?format=json&query=reviewed:yes"

    response = requests.get(url)
    nodes = json.loads(response.text)['nodes']

    for node in nodes:
        fetch_node_data(node)

        for enzyme_class in enzyme_class_list:
            f.write(f"{enzyme_class[0]}\t{enzyme_class[1]}\n")
            f.flush()

        enzyme_class_list.clear()

    f.close()


def crawling_enzyme_info():
    # browser = webdriver.Firefox(executable_path=r'D:\Util\geckodriver-v0.29.0-win64\geckodriver.exe')
    browser = webdriver.Chrome(executable_path=r'D:\Util\chromedriver_win32\chromedriver.exe')
    browser.get('https://www.uniprot.org/uniprot/?query=reviewed:yes#customize-columns')

    browser.find_element_by_id('annotation_score-column-input').click()
    browser.find_element_by_id('top-customize-columns-save').click()

    with open(r'C:\Users\duvee\Desktop\enzyme_class_list.tsv', 'r') as f:
        for line in f:
            line = line.strip().split('\t')
            enzyme_class = line[0]

            url = f'https://www.uniprot.org/uniprot/?' \
                  f'query=ec%3A{enzyme_class}+reviewed%3Ayes+existence%3A"evidence+at+protein+level+[1]"&' \
                  f'sort=annotation_score&' \
                  f'limit=1000'

            browser.get(url)
            time.sleep(0.2)

            # 결과 없으면 패스
            try:
                browser.find_element_by_id('noResultsMessage')
                continue
            except NoSuchElementException:
                print(f"Download: {enzyme_class}")

            browser.find_element_by_id('download-button').click()
            time.sleep(0.1)

            browser.find_element_by_id('menu-go').click()
            time.sleep(0.5)


if __name__ == '__main__':
    # crawling_enzyme_class_list()
    crawling_enzyme_info()
