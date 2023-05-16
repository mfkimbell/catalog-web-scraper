# STL
from typing import Dict
from flask import Flask, render_template, request
from psycopg2 import sql


# PDM
import psycopg2
from psycopg2 import extensions as pg2


def connect(url: str) -> pg2.connection:
    return psycopg2.connect(dsn=url)


app = Flask(__name_)


@app.route("/")
def student():
    return render_template("home.html")


@app.route("/books", methods=["POST", "GET"])
def result():
    return render_template("books.html")


@app.route("/books/query", methods=["POST"])
def query():
    if request.method == "POST":
        res = request.form
        book_name = res["search-bar"]
        db = psycopg2.connect(
            database="postgres",
            user="postgres",
            password="password",
            host="127.0.0.1",
            port="5432",
        )
        cursor = db.cursor()

        finalresult = []

        book_query = sql.SQL(
            """
                SELECT * FROM books WHERE upc = (
                    SELECT UPC FROM books 
                    WHERE name ILIKE {book_name} )
            """
        ).format(book_id=sql.Literal(f"{book_name}"))

        cursor.execute(book_query)

        result1 = cursor.fetchall()

        category_query = sql.SQL(
            """
                    SELECT category
                    FROM books_to_category
                    JOIN categories ON category_id = id
                    WHERE upc = (
                        SELECT UPC FROM books 
                        WHERE name ILIKE {book_name} )
                """
        ).format(book_id=sql.Literal(f"{book_name}"))

        cursor.execute(category_query)

        result2 = cursor.fetchall()

        result1 = list(result1[0])

        result_cat = []

        for item in result2:
            result_cat.append(item[0])

        result1.append(result_cat)

        finalresult.append(result1)
        return finalresult


if __name__ == "__main__":
    app.run(debug=True)
