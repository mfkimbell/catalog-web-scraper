# webScraper
Using HTTP requests, Xpaths, and xlml python module to return HTML elements in ways we can extract data from a webpage. We are using these tools to search through a book catalogue website.

![Screenshot 2023-02-03 at 12 42 26 PM](https://user-images.githubusercontent.com/107063397/216682300-bb6e8fae-3682-4a53-9e2b-c04747c796b6.png)


We are going to be storing info in JSON files, so we import that library. 

Sxpath is our lab's custom method for xpath's that bypasses smart strings to ensure to prevent memory leaks.

RabbitPSQLMixin is a class that helps us create objects in order to transfer messages to RabbitMQ as well as PostgreSQL.
The confige file contains the data necessary for the computer to talk to both RabbitMQ and PostgreSQL as well.
Here is a generic template.

<img width="340" alt="Screenshot 2023-01-30 at 6 03 09 PM" src="https://user-images.githubusercontent.com/107063397/215624687-a36ef030-d597-4dae-ba5d-f039d2c93d35.png">

I used a Makefile to create some shortcuts for rerunning and rebuilding the docker container. 

<img width="687" alt="Screenshot 2023-01-30 at 6 14 38 PM" src="https://user-images.githubusercontent.com/107063397/215625783-39ea60f6-1f8d-4549-86b0-efef67d83bb0.png">

Build rebuilds the docker container, and force-build forces it to remake the docker container from scratch, ignoring the cache from it's previous attempt to build. Up and run both run the python file but with different permissions. 

The docker container is a standalone package of software that allows the user to run your application without having to worry about all the dependencies that are required by your program. Here, my docker file is executing code from some SQL that I have written with a shell script.

<img width="551" alt="Screenshot 2023-01-30 at 6 08 36 PM" src="https://user-images.githubusercontent.com/107063397/215625108-2e8e6f90-d9e6-48ab-bacb-08ca3375024d.png">

In the shell script, I am creating the postgres database as well as inserting the main table by initializing the sql file. 

<img width="439" alt="Screenshot 2023-01-30 at 6 14 11 PM" src="https://user-images.githubusercontent.com/107063397/215625735-4a8c9c28-110f-408b-8370-1c40a0a233b2.png">

![Screenshot 2023-02-03 at 12 43 00 PM](https://user-images.githubusercontent.com/107063397/216682326-9629ffad-10fc-4f1c-b34d-838cc6ab17d6.png)

lxml is a parsing tool that, in conjunction with the requests module, allows us to collect specific data from webpages. In this example, the worker is selecting the list of genre's from the left side of the main page and collecting the url from each hyperlink. It then uses those hyperlinks to call work on the those pages.

Here's a visual representation marked with a # "1".

<img width="480" alt="Screenshot 2023-01-23 at 6 46 38 PM" src="https://user-images.githubusercontent.com/107063397/214188598-87bce61b-8025-4de2-8476-89b153313691.png">

The next step is to gather information from specific books. In order to do that, we have to navigate to the individual book pages. Shown previously with the number "2". 

Another issue is that each book genre has multiple pages of books, so we have to continue to naviagate to the "next" button if the page has one while we sort through books. The way we solve this is by having the docker command queue the next object to be parsed. 

In other words, a worker who's job is to accept the "main_page" will request a "genre_page" worker for every genre on the main page. A genre worker will both call another "genre_page" worker for the next page (if there is a next page) as well as call a "book_page" worker for each book on the genre page. The "book_page" worker will collect the necessary information from the book and add that data to the postgres table that was created earlier. 

When we create the scraper class, we give it a function that allows it to queue on RabbitMQ with the correct connection data from the config.

<img width="623" alt="Screenshot 2023-01-30 at 6 22 02 PM" src="https://user-images.githubusercontent.com/107063397/215628906-c95a0b69-60d7-44c7-b5b9-cfe1616b94fd.png">

In the main function, we initialize the Scraper, queue work for "main_page" "genre_page" and "book_page" workers, and publish the main page to be recieved by a "main_page" worker.

<img width="478" alt="Screenshot 2023-01-30 at 6 24 21 PM" src="https://user-images.githubusercontent.com/107063397/215629108-b6cc8667-fcbd-4e43-8d83-02a615f45be9.png">

The following is for the "main_page" worker, which collects URLS and calls for "genre_page" workers.
<img width="461" alt="Screenshot 2023-01-30 at 6 22 17 PM" src="https://user-images.githubusercontent.com/107063397/215629503-e77b5ef0-aa67-4d45-b972-f63d7c7d8b81.png">

Here, the "genre_page" worker checks if there is a next page, and if so, calls for another "genre_page" worker. Additionally, collects all of the URLs for the book links, and calls a "book_page" worker for each one. 

<img width="580" alt="Screenshot 2023-01-30 at 6 22 29 PM" src="https://user-images.githubusercontent.com/107063397/215629658-ac27298c-ce05-442e-975f-a50afdc3524f.png">

Finally, the "book_page" worker collects all of the desired data from the book page's URL and then stores that data into an postgreSQL table.

This is a visual demonstration of the "book worker's" data:

<img width="380" alt="Screenshot 2023-01-23 at 6 55 50 PM" src="https://user-images.githubusercontent.com/107063397/214191115-f994f5a8-4f54-4fab-9f96-686023eae4f8.png">

And here are examples of the relational database data. 


This is an example of a book record:

<img width="853" alt="Screenshot 2023-02-03 at 12 24 13 PM" src="https://user-images.githubusercontent.com/107063397/216784549-3f7df12c-aa86-456c-8cac-a9d70846876c.png">

This is what the categories table looks like:

<img width="377" alt="Screenshot 2023-02-03 at 12 23 21 PM" src="https://user-images.githubusercontent.com/107063397/216784572-88ae8dd0-2efc-40de-afa2-cde91f566cab.png">

And here is the table relating those data:

<img width="344" alt="Screenshot 2023-02-03 at 12 22 52 PM" src="https://user-images.githubusercontent.com/107063397/216784574-66c01207-3616-4555-b348-b73197461767.png">

Here is proof the scraper works, producing all of the books and categories in the count for those tables:

![Screenshot 2023-02-03 at 11 03 56 AM](https://user-images.githubusercontent.com/107063397/216784656-3e2f3620-97f0-43db-abf6-9250dd9b69ce.png)

![Screenshot 2023-02-03 at 11 04 20 AM](https://user-images.githubusercontent.com/107063397/216784662-e79de939-8f18-4b4a-b15c-21628cb3c961.png)



