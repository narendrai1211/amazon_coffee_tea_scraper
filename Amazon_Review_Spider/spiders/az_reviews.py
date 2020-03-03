# -*- coding: utf-8 -*-
import json
import scrapy
import time
from bs4 import BeautifulSoup
import selenium.webdriver
import os
from scrapy import Request


class AzReviewsSpider(scrapy.Spider):
    start_time = time.time()
    name = 'az_reviews'
    start_urls = [
        'https://www.amazon.in/Coffee-Tea-Beverages/b/?ie=UTF8&node=4859478031&ref_=sv_topnav_storetab_gourmet_4',
    ]
    main_data_list = []
    url_list = []
    list_byf = []
    current_page = 1
    list_mention = []
    json_by_feature = {}
    json_group_by_rating = {}
    set_mention = set()
    reviews_list = []
    images_dir = 'author_images'
    reviews_collection = 'reviews_output'
    next_page = ''
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
    }

    def start_requests(self):
        try:
            os.mkdir(self.reviews_collection)
        except Exception as e:
            print(e)
        for i in self.start_urls:
            yield Request(i, headers=self.headers, callback=self.parse)

    def populate_mention_list(self, set_mention):
        for i in set_mention:
            self.list_mention.append(i)
        if '' in self.list_mention:
            self.list_mention.remove('')
        return self.list_mention

    def clear_data(self):
        self.main_data_list.clear()
        self.list_byf.clear()
        self.list_mention.clear()
        self.set_mention.clear()

    def get_product_urls(self, response):
        self.url_list.clear()
        print(response.url)
        print('Current URL', response.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        time.sleep(5)
        if response.url == self.start_urls[0]:
            next_page_url = soup.find_all('a', {'id': 'pagnNextLink'})
            for i_nextp in next_page_url:
                url = 'https://www.amazon.in' + i_nextp['href']
                print(url)
                time.sleep(5)
                self.next_page = url
            all_links = soup.find_all('a',
                                      class_='a-link-normal s-access-detail-page s-color-twister-title-link a-text-normal')  # noqa
            for i_each in all_links:
                link = i_each['href']
                if i_each.text.startswith('[Sponsored]'):
                    j = 'https://www.amazon.in' + i_each['href']
                    self.url_list.append(j)
                else:
                    self.url_list.append(link)
        else:
            next_page_url = soup.find_all('li', {'class': 'a-last'})
            for i_nextp in next_page_url:
                url = 'https://www.amazon.in' + i_nextp.find('a')['href']
                print(url)
                # time.sleep(5)
                self.next_page = url
            d = soup.find_all('div', class_='s-result-list s-search-results sg-row')
            for i in d:
                links = i.find_all('a', class_='a-link-normal a-text-normal')
                for i_each in links:
                    print(i_each['href'])
                    link = 'https://www.amazon.in' + i_each['href']
                    self.url_list.append(link)
        print(self.url_list)
        return self.url_list

    def list_to_dictionary(self, key_rating):
        iterate_over_list = iter(key_rating)
        self.json_by_feature = dict(zip(iterate_over_list, iterate_over_list))
        return self.json_by_feature

    def write_data_to_file(self, file_name, main_stats_list):
        dumped = json.dumps(main_stats_list, indent=4, ensure_ascii=False)
        with open(file_name, 'w') as f:
            f.write(dumped)

    def populate_reviews_on_page(self, driver):
        all_images = []
        date = []
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        self.reviews_list.clear()
        title_of = soup.find('title')
        title_of_page = title_of.text.split(',')[0].lower()
        all_revs = soup.find_all('div', {'data-hook': 'review'})
        for i_each_review in all_revs:
            helpful_cnt = ''
            list_images_url = ''
            review_title = ''
            review_date = ''
            rating_given = ''
            review_author = ''
            review_body = ''
            try:
                helpful_cnt = i_each_review.find('span', {'data-hook': 'helpful-vote-statement'}).text.split(' ')[
                    0].strip()
                if helpful_cnt == 'One':
                    helpful_cnt = '1'
            except Exception as e:
                print('Exception in HELPFUL', e)
            try:
                rating_given = i_each_review.find('i', {'data-hook': 'review-star-rating'}).text.split(' ')[0].strip()
            except Exception as e:
                rating_given = i_each_review.find('i', {'data-hook': 'cmps-review-star-rating'}).text.split(' ')[
                    0].strip()
                print('Exception in rating given Assigned new value to it', e)

            try:
                review_title = i_each_review.find('a', {'data-hook': 'review-title'}).text.strip()
            except Exception as e:
                review_title = i_each_review.find('span', {'data-hook': 'review-title'}).text.strip()
                print('Exception in review_title Assigned New Value to it', e)
            try:
                review_body = i_each_review.find('div', {'data-hook': 'review-collapsed'}).text.strip()
            except Exception as e:
                print('Exception in review body', e)
            try:
                user_dp = i_each_review.find_all('div', {'class': 'a-profile-avatar'})
                list_images_url = ''.join(i.find('img')['data-src'] for i in user_dp)
                all_images.append(list_images_url)
            except Exception as e:
                print('Exception in DP', e)
            try:
                review_date = i_each_review.find('span', {'data-hook': 'review-date'}).text.split('on')[1].strip()
            except Exception as e:
                print('In review date exception', e)
            try:
                review_author = i_each_review.find('span', {'class': 'a-profile-name'}).text
            except Exception as e:
                print('Author Exception Name', e)

            json_record = {
                'review_title': review_title,
                'date': review_date,
                'author_name': review_author,
                'author_picture': list_images_url,
                'rating': rating_given,
                'review_body': review_body,
                'found_helpful': helpful_cnt,
            }
            print(json_record)
            self.reviews_list.append(json_record)
        return self.reviews_list

    def parse(self, response):
        self.url_list = self.get_product_urls(response)
        path = os.getcwd() + '/chromedriver'
        print(path)
        time.sleep(5)
        driver = selenium.webdriver.Chrome(path)
        for i in self.url_list:
            driver.get(url=i)
            self.clear_data()
            time.sleep(5)
            by_f = ''
            key_rating = []
            rating_num = int()
            avg_rating = ''
            try:
                driver.find_element_by_xpath('//*[@id="cr-summarization-attributes-list"]/div[4]/a').click()
                time.sleep(3)
            except Exception as e:
                print(e)
            try:
                by_f = driver.find_element_by_id('cr-summarization-attributes-list').text
                key_rating = by_f.split('\n')
                if 'See less' in key_rating:
                    key_rating.pop()  # to remove last element
            except Exception as e:
                print(e)
                print('By feature Rating Not found for this page')
            self.json_by_feature = self.list_to_dictionary(key_rating)
            try:
                # //*[@id="reviewsMedley"]/div/div[1]/div[2]/div[1]/div/div[2]/div/span/span
                average_rating_text = driver.find_element_by_xpath(
                    '//*[@id="reviewsMedley"]/div/div[1]/div[2]/div[1]/div/div[2]/div/span/span/a/span').text
                avg_rating = average_rating_text.split('out of')[0].strip()
            except Exception as e:
                average_rating_text = driver.find_element_by_xpath(
                    '//*[@id="reviewsMedley"]/div/div[1]/div[2]/div[1]/div/div[2]/div/span/span').text
                avg_rating = average_rating_text.split('out of')[0].strip()
                print(e)
            if avg_rating == '':
                try:
                    average_rating_text = driver.find_element_by_xpath(
                        '//*[@id="reviewsMedley"]/div/div[1]/div[2]/div[1]/div/div[2]/div/span/span').text
                    avg_rating = average_rating_text.split('out of')[0].strip()
                except Exception as e:
                    print(e)
            try:
                total_ratings_str = driver.find_element_by_xpath(
                    '//*[@id="reviewsMedley"]/div/div[1]/div[2]/div[2]/span').text  # noqa
                print('rating str', total_ratings_str)
                rating_num = total_ratings_str.split(' ')[0]
                print(rating_num)
            except Exception as e:
                print(e)
            try:
                d = driver.find_element_by_class_name('cr-lighthouse-terms')
                span_tags = d.find_elements_by_tag_name('span')
                for i_span in span_tags:
                    self.set_mention.add(i_span.text)
            except Exception as e:
                print(e)
            rating_group = ''
            percent_rating = ''
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            title_of = soup.find('title')
            title_of_page = title_of.text
            for i_row in range(1, 6):
                try:
                    rating_group = driver.find_element_by_xpath(
                        '//*[@id="histogramTable"]/tbody/tr[' + str(i_row) + ']/td[1]/span[1]/a').text  # noqa
                    percent_rating = driver.find_element_by_xpath(
                        '//*[@id="histogramTable"]/tbody/tr[' + str(i_row) + ']/td[3]/span[2]/a').text  # noqa
                    self.json_group_by_rating.update({rating_group: percent_rating})
                except Exception as e:
                    rating_group = driver.find_element_by_xpath(
                        '//*[@id="histogramTable"]/tbody/tr[' + str(i_row) + ']/td[1]/span[1]').text  # noqa
                    percent_rating = driver.find_element_by_xpath(
                        '//*[@id="histogramTable"]/tbody/tr[' + str(i_row) + ']/td[3]/span[2]').text  # noqa
                    print(e)
                    self.json_group_by_rating.update({rating_group: percent_rating})

            self.reviews_list = self.populate_reviews_on_page(driver)
            self.list_mention = self.populate_mention_list(self.set_mention)
            json_record = {
                'product_name': title_of_page,
                'total_ratings': rating_num,
                'average_rating': avg_rating,
                'groups_by_rating': self.json_group_by_rating,
                'mention_keywords': self.list_mention,
                'ratings_by_feature': self.json_by_feature,
                'reviews': self.reviews_list
            }
            self.main_data_list.append(json_record)
            file_name = title_of_page + '.json'
            d = os.getcwd()
            path = d + '/reviews_output/' + file_name
            print(path)
            self.write_data_to_file(path, self.main_data_list)
        driver.close()
        total_time = time.time() - self.start_time
        print(total_time)
        print(self.next_page)
        self.current_page += 1
        if self.current_page < 4:
            yield Request(self.next_page,
                          dont_filter=True,
                          headers=self.headers,
                          callback=self.parse
                          )
        else:
            print("Done Scraping")
