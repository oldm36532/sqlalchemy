import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_engine():
    """Create and return a SQLAlchemy engine from DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise ValueError("DATABASE_URL is not set")
    # TODO: create the engine; handle a missing URL gracefully
    return create_engine(url)


def store_report(engine):
    """Print counts, the catalog, and the top 3 customers."""
    with engine.connect() as conn:
        users=conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        products=conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        orders=conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        print("users:",users,"products:",products,"orders:",orders)
        Products_table=conn.execute(text("SELECT name,price,stock FROM products ORDER BY name"))
        for row in Products_table:
            print(row.name,"-",row.price,"-",row.stock)
        Top_3=conn.execute(text("""
            SELECT u.full_name,SUM(o.quantity) as total
            FROM orders as o
            INNER JOIN users as u ON o.user_id = u.id
            GROUP BY u.id
            ORDER BY SUM(o.quantity) DESC
            LIMIT 3
            """))
        for row in Top_3:
         print(row.full_name,"-",row.total)

        # TODO: COUNT(*) on users, products, orders
        # TODO: SELECT name, price, stock FROM products ORDER BY name
        # TODO: top 3 customers by SUM(quantity) via a join + GROUP BY
        ...


def add_product(engine, name, category, price, stock):
    """INSERT a product and return its new id."""
    with engine.begin() as conn:
        added_product=conn.execute(text("""
        INSERT INTO products(name,category,price,stock)
        VALUES (:name,:category,:price,:stock)
        RETURNING id
        """),
        {"name":name,"category":category,"price":price,"stock":stock},)
        return added_product.scalar()

        # begin() commits automatically at the end
        # TODO: INSERT ... RETURNING id, with named parameters (include category)
        ...


def place_order(engine, email, product_name, quantity):
    """Create an order and decrement stock in one transaction."""
    with engine.begin() as conn:
        user_id=conn.execute(text("SELECT id FROM users WHERE email=:email"),{"email":email}).scalar()
        product_info=conn.execute(text("SELECT id,stock FROM products WHERE name=:product_name"),
        {"product_name":product_name}).fetchone()
        if not product_info:
            raise ValueError(f"Product {product_name} does not exist")
        product_id=product_info[0]
        current_stock=product_info[1]
        if current_stock < quantity:
            raise ValueError(f"Product {product_name} has only {current_stock} stock")
        order=conn.execute(text("""
         INSERT INTO orders(user_id,product_id,quantity)
        VALUES (:user_id,:product_id,:quantity)
            """),
        {"user_id":user_id,"product_id":product_id,"quantity":quantity},)
        conn.execute(text("""
        UPDATE products
        SET stock=stock-:quantity
        WHERE id=:product_id
                          """),
                     {"quantity":quantity,"product_id":product_id}
                     )


        # begin() commits on success, rolls back on error
        # TODO: look up user_id by email and product (id + stock) by name
        # TODO: if stock < quantity, raise an error to trigger rollback
        # TODO: INSERT the order, then UPDATE the product's stock
        ...


def main():
    engine = get_engine()
    while True:
        print("Welcome to Dashboard")
        print("1.Store report")
        print("2.Add product")
        print("3.Place order")
        print("4.Exit")
        choice=input("Enter your choice:")
        if choice=="1":
            store_report(engine)
        elif choice=="2":
            name=input("Enter product name:")
            category=input("Enter product category:")
            price=int(input("Enter product price:"))
            stock=int(input("Enter product stock:"))
            new_product_id=add_product(engine, name, category, price, stock)
            print(f"New was added its id:{new_product_id}")
        elif choice=="3":
            email=input("Enter email:")
            product_name=input("Enter product name:")
            quantity=int(input("Enter quantity:"))
            try:
                place_order(engine, email, product_name, quantity)
            except Exception as e:
                print("Error:",e)
        elif choice=="4":
            print("Thank you for using this program")
            break
        else:
            print("Please enter a valid choice")

    # TODO: a small menu to add a product or place an order


if __name__ == "__main__":
    main()
