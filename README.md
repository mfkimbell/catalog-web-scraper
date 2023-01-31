# webScraper
Using HTTP requests, Xpaths, and xlml python module to return HTML elements in ways we can extract data from a webpage. We are using these tools to search through a book catalogue website.

<img width="467" alt="Screenshot 2023-01-30 at 4 57 13 PM" src="https://user-images.githubusercontent.com/107063397/215615364-d109a7c8-f845-463d-b666-643f2a8b4de2.png">

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


<img width="415" alt="Screenshot 2023-01-30 at 6 12 40 PM" src="https://user-images.githubusercontent.com/107063397/215625566-4d3da647-c424-49e5-b0f3-a63ca88472ec.png">

lxml is a parsing tool that, in conjunction with the requests module, allows us to collect specific data from webpages. In this example, I am selecting the list of genre's from the left side of the main page, and I am collecting the url from each hyperlink. I can then use those hyperlinks to traverse through the links in order by using a loop. 

Here's a visual representation marked with a # "1".

<img width="890" alt="Screenshot 2023-01-23 at 6 46 38 PM" src="https://user-images.githubusercontent.com/107063397/214188598-87bce61b-8025-4de2-8476-89b153313691.png">

And here's the code corresponding:



The next step is to gather information from specific books. In order to do that, we have to navigate to the individual book pages. Shown previously with the number "2". 

Another issue is that each book genre has multiple pages of books, so we have to continue to naviagate to the "next" button if the page has one while we sort through books. The way we solve this is by having the docker command queue the next object to be parsed. 

In other words, a worker who's job is to accept the home page will request a "genre page" worker for every genre on the main page. A genre worker will both call another genre worker for the next page (if there is a next page) as well as call a worker for each book on the genre page. The "book page" worker will collect the necessary information from the book and add that data to the postgres table that was created earlier. 



Finally, we have to collect data from individual books and organize that data. 

<img width="680" alt="Screenshot 2023-01-23 at 6 55 50 PM" src="https://user-images.githubusercontent.com/107063397/214191115-f994f5a8-4f54-4fab-9f96-686023eae4f8.png">

The following code creates a "book" object with all of our desired data targets and stores all of the books in a list called "books".

<img width="765" alt="Screenshot 2023-01-23 at 6 56 47 PM" src="https://user-images.githubusercontent.com/107063397/214191222-35260871-d979-40f9-a928-570618adb8e3.png">

With this, we can determine things like the average cost of books as shown below.

<img width="399" alt="Screenshot 2023-01-23 at 7 24 04 PM" src="https://user-images.githubusercontent.com/107063397/214193979-800c0d90-9bbf-4b31-ae2e-21c1a57d4b43.png">

<img width="283" alt="Screenshot 2023-01-23 at 7 23 50 PM" src="https://user-images.githubusercontent.com/107063397/214193958-79e94860-9036-4465-b36c-1b96b65322ba.png">


The next step in the project is to submit that data into postgreSQL, which I am in the process of completing as of Janurary 23, 2023.







