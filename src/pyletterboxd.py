import requests
from bs4 import BeautifulSoup

class Letterboxd:
	def __init__(self, username=None, password=None, session=requests.session()):
		"""
		Parameters
		----------
		username : str
			letterboxd username
		password : str
			letterboxd password
		session : requests.session
			use a session or default session
		"""

		if username and password and not session.cookies.get_dict.get(
				"letterboxd.signed.in.as"):
			try:
				self.session = letterboxd_session(username, password)
			except:
				print("A letterboxd session could not be established. Is selenium installed?")
				print()
				print("Continuing with default session...")
				self.session = session
		else:
			self.session = session

	def get(self, url, is_film=True):
		lb = LetterboxdFilm() if is_film else LetterboxdList()

		return lb.get(url, session=self.session)

	def get_dict(self, url, is_film=True):
		lb = LetterboxdFilm() if is_film else LetterboxdList()

		return lb.get(url, session=self.session).to_dict()

	def get_films(self, film_urls):
		films = {}

		for film_url in film_urls:
			films[film_url] = self.get(film_url)

		return films

	def get_films_dict(self, film_urls):
		return {k:v.to_dict() for k, v in self.get_film(film_urls).items()}

	def user_lists(self, username):
		lists_url = f'https://letterboxd.com/{username}/lists'
		film_lists = {}

		for page_num in page_range(session.get(lists_url).text):
			html = session.get(f'{lists_url}/page/{page_num}').text
			litag = BeautifulSoup(html, 'lxml').find('section', {'class': 'list-set'})
			lists = litag.find_all('section')
			page_links = [pt.find('a').get('href') for pt in lists]
			list_urls = [f'https://letterboxd.com{link}' for link in page_links]
			film_lists = {**film_lists, **{list_url:self.get(
					list_url, is_film=False) for list_url in list_urls}}

		return film_lists

	def user_lists_dict(self, username):
		return {k:v.to_dict() for k, v in self.user_lists(username).items()}


class LetterboxdList:
	film_urls = []

	def get(list_url, session=requests):
		self.username, self.listname = user_and_list_name(self.list_url)
		self.list_url = cleanurl(list_url)
		html = session.get(self.list_url).text
		lists_data = {}

		for page_num in page_range(html):
			html = session.get(f'{self.list_url}page/{page_num}').text
			soup = BeautifulSoup(html, features='lxml')
			postertags = soup.find_all('li', {'class': 'poster-container'})
			page_links = [pt.find("div")["data-target-link"] for pt in postertags]
			self.film_urls += [f'https://letterboxd.com{pl}' for pl in page_links]

		return self

	def to_dict(self):
		return {
			"username": self.username, 
			"listname": self.listname,
			"list_url": self.list_url,
			"film_urls": self.film_urls
		}


class LetterboxdFilm:
	def get(self, film_url, session=requests.session()):
		self.film_url = cleanurl(film_url)
		req = session.get(self.film_url)
		soup = BeautifulSoup(req.text, 'lxml')
		bddiv = soup.find('div', id='backdrop')
		backdrop_list = ['data-backdropmobile', 'data-backdrop', 'data-backdrop2x']
		script = str(soup.find('script', {'type': 'application/ld+json'}))
		start = script.find('{')
		data = eval(script[ start: script[start:].find('\n')+start ])
		poster_front = data.get('image')[0:data.get('image').find('-0-')]
		poster_sizes = ['-0-230-0-345-crop.jpg', '-0-460-0-690-crop.jpg', 
				'-0-500-0-700-crop.jpg', '-0-1000-0-1500-crop.jpg']

		self.tmdb_id = soup.body.get("data-tmdb-id")
		self.lbxd_id = soup.find("a", id='poster-zoom').find('div')["data-film-id"]
		self.lbxd_uri = soup.find('div', {'class': 'urlgroup'}).find('input').get('value')
		self.backdrops = [bddiv.get(dbd)[:bddiv.get(dbd).find('?')
				] for dbd in backdrop_list] if bddiv.get('data-backdrop') else ['', '', '']
		self.posters = [f'{poster_front}{ps}crop.jpg' for ps in poster_sizes
				] if poster_front else ['', '', '']
		self.description = soup.find('div', {'class': 'truncate'}).p.text
		self.rating = data.get('aggregateRating', {}).get('ratingValue')
		self.genre = data.get('genre')
		self.title = data.get('name')
		self.year = soup.find('small', {'class': 'number'}).find('a').text
		self.is_watched = True if soup.find('input', id='frm-rewatch') else False
		details_page = session.get(f'{film_url}details/')
		alt_title_str = soup.find('div', {'class': 'text-indentedlist'}).find('p').text
		self.alternate_titles = alt_title_str.replace('\t', '').replace('\n', '').split(',')
		return self

	def to_dict(self):
		return {
			'film_url': self.film_url,
			'tmdbID': self.tmdb_id,
			'LetterboxdID': self.lbxd_id,
			'LetterboxdURI': self.lbxd_uri,
			'posters': self.posters,
			'backdrops': self.backdrops,
			'genres': self.genre,
			'title': self.title,
			'alternate_titles': self.alternate_titles,
			'year': self.year,
			'description': self.description,
			'rating': self.rating,
			'is_watched': self.is_watched
		}


def letterboxd_session(username, password, session=requests.session()):
	from selenium import webdriver
	from selenium.webdriver.common.by import By
	from selenium.webdriver.common.keys import Keys
	from selenium.webdriver.chrome.options import Options
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.support import expected_conditions as EC

	options = Options()
	options.add_argument("--no-sandbox")
	options.add_argument("--disable-gpu")
	options.add_argument("--headless")
	options.add_argument("--disable-dev-shm-usage")

	driver = webdriver.Chrome(options=options)
	driver.get("https://letterboxd.com/sign-in-popup")
	WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
			(By.NAME, 'username')))

	user = driver.find_element(By.NAME, "username")
	passwd = driver.find_element(By.NAME, "password")
	user.send_keys(username)
	passwd.send_keys(password)
	passwd.send_keys(Keys.ENTER)

	cookies = driver.get_cookies()
	session = requests.session()

	driver.quit()

	for cookie in cookies:
		session.cookies.set(cookie['name'], cookie['value'])

	return session


def page_range(self, html):
	li_tags = BeautifulSoup(html,"lxml").find_all(
			"li", {"class": "paginate-page"})

	return range(1, int(li_tags[-1].find("a").text)+1) if li_tags else range(1, 2)


def cleanurl(url):
	return url if url.endswith('/') else f'{url}/'


def user_and_list_name(list_url):
	return [key for key in list_url.split("/") if key not in [
		'http:', 
		'https:', '', 
		'letterboxd.com', 
		'www.letterboxd.com',
		'list',
		'reviews']
	]
	

# def letterboxd_export(list_url, session=requests, path):
# 	csv_str = csv_export(films)
# 	tmp_path = Path(tmpdir).joinpath('export.csv')
# 	tmp_path.write_text(export)
# 	films = lget(list_url, session=session)


# def csv_export(films):
# 	export = 'LetterboxdURI, tmdbID\n'
# 	for film in films.values():
# 		export += f'{film.get("LetterboxdURI")}, {film.get("tmdbID")}\n'
# 	return export


# def letterboxd_import(path_to_csv, driver, **kwargs):
# 	driver.get('https://letterboxd.com/list/new')	
# 	for k, v in kwargs.items():
# 		try:
# 			elem = driver.find_element(By.NAME, k)
# 			elem.send_keys(v)
# 		except:
# 			print(f'No element named: {k}')
# 	str(path_to_csv)
# 	import_button = driver.find_element(By.NAME, 'file')
# 	import_button.send_keys(str(tmp_path))
# 	import_button.send_keys(Keys.ENTER)
# 	WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
# 			(By.XPATH, '//*[@id="content"]/div/div/a[2]')))
# 	driver.find_element(By.XPATH, '//*[@id="content"]/div/div/a[2]').click()
# 	driver.find_element(By.ID, 'list-edit-save').click()

# 	return True