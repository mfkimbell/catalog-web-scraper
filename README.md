# webScraper
Using HTTP requests, Xpaths, and xlml python module to return HTML elements in ways we can extract data from a webpage. We are using these tools to search through a book catalogue website.

lxml is a parsing tool that, in conjunction with the requests module, allows us to collect specific data from webpages. In this example, I am selecting the list of genre's from the left side of the main page, and I am collecting the url from each hyperlink. I can then use those hyperlinks to traverse through the links in order by using a loop. 

Here's a visual representation marked with a # "1".

<img width="890" alt="Screenshot 2023-01-23 at 6 46 38 PM" src="https://user-images.githubusercontent.com/107063397/214188598-87bce61b-8025-4de2-8476-89b153313691.png">


And here's the code corresponding:

Here is colleging all of the HTML from the page.

<img width="591" alt="Screenshot 2023-01-23 at 6 49 41 PM" src="https://user-images.githubusercontent.com/107063397/214189500-62633552-8b16-4216-b8aa-509969844452.png">

This is the code collecting the genre pages.

<img width="543" alt="Screenshot 2023-01-23 at 6 50 24 PM" src="https://user-images.githubusercontent.com/107063397/214189717-22f67710-784d-47d8-915b-ab828e7f0398.png">

<img width="373" alt="Screenshot 2023-01-23 at 6 51 08 PM" src="https://user-images.githubusercontent.com/107063397/214189925-9ec76b72-8b41-4ef8-9e3e-69ae1a88a673.png">

The next step is to gather information from specific books. In order to do that, we have to navigate to the individual book pages. Shown previously with the number "2". Another issue is that each book genre has multiple pages of books, so we have to continue to naviagate to the "next" button if the page has one while we sort through books. That is what the while loop in the following code is doing. It is continuing to navigate to pages as long as the "next-page" function continues to return a valid value. 

<img width="667" alt="Screenshot 2023-01-23 at 6 53 15 PM" src="https://user-images.githubusercontent.com/107063397/214190532-a1811167-1bad-4db5-be3c-c7a591db5d9f.png">

The code prints the pages URL as it navigates from page to page:

<img width="703" alt="Screenshot 2023-01-23 at 7 00 48 PM" src="https://user-images.githubusercontent.com/107063397/214191713-5387d670-184b-4d3d-9a58-a405f996c912.png">


Finally, we have to collect data from individual books and organize that data. 

<img width="680" alt="Screenshot 2023-01-23 at 6 55 50 PM" src="https://user-images.githubusercontent.com/107063397/214191115-f994f5a8-4f54-4fab-9f96-686023eae4f8.png">

The following code creates a "book" object with all of our desired data targets and stores all of the books in a list called "books".

<img width="765" alt="Screenshot 2023-01-23 at 6 56 47 PM" src="https://user-images.githubusercontent.com/107063397/214191222-35260871-d979-40f9-a928-570618adb8e3.png">

With this, we can determine things like the average cost of books as shown below.

<img width="399" alt="Screenshot 2023-01-23 at 7 24 04 PM" src="https://user-images.githubusercontent.com/107063397/214193979-800c0d90-9bbf-4b31-ae2e-21c1a57d4b43.png">

<img width="283" alt="Screenshot 2023-01-23 at 7 23 50 PM" src="https://user-images.githubusercontent.com/107063397/214193958-79e94860-9036-4465-b36c-1b96b65322ba.png">


The next step in the project is to submit that data into postgreSQL, which I am in the process of completing as of Janurary 23, 2023.







