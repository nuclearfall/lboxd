# pyletterboxd
A python library for accessing list and film data from letterboxd.

NOTE: This library is in no way affiliated with letterboxd.com. It is meant for
education purposes only. Letterboxd does not have an official API.


## example usage:
```
import pyletterboxd as lboxd

film = lboxd.LetterboxdFilm().get(<film_url>)
lblist = lboxd.LetterboxdList().get(<list_url>)
```

It also supports logging into your account, but you must have selenium and Chrome installed.
You may enter login credentials or use a previous session.

```
import pyletterboxd as lboxd

lb = lboxd.Letterboxd(<username>, <password>) 
lb = lboxd.Letterboxd(session=<requests_session>)

box_list = lb.get(<list url>, is_film=False)
### You may also use get_dict
film_dict = lb.get_films_dict(box_list.film_urls)
### get all lists of a user
film_lists = lb.user_lists(<username>)
```




