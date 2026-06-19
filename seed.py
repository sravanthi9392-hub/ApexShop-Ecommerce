# seed.py
from app import app
from models import db, Product

def seed_database():
    with app.app_context():
        # FIX: This line automatically creates the database file and all required tables
        db.create_all()

        # Check if products already exist to avoid duplicate injection
        if Product.query.count() > 0:
            print("Database already contains items. Seeding canceled.")
            return

        simple_products = [
            # === ELECTRONICS ===
            Product(
                name="Wireless Mouse",
                description="Ergonomic 2.4GHz wireless optical mouse with USB receiver.",
                category="Electronics",
                price=15.99,
                stock_quantity=100,
                image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500"
            ),
            Product(
                name="Bluetooth Headphones",
                description="Over-ear wireless headphones with noise isolation and deep bass.",
                category="Electronics",
                price=39.99,
                stock_quantity=50,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
            ),
            Product(
                name="USB-C Charging Cable",
                description="Durable 6ft nylon braided fast-charging cable.",
                category="Electronics",
                price=9.99,
                stock_quantity=200,
                image_url="https://images.unsplash.com/photo-1543269664-76bc3997d9ea?w=500"
            ),
            Product(
                name="Smartphone Stand",
                description="Adjustable aluminum desktop holder for iPhones and Androids.",
                category="Electronics",
                price=12.50,
                stock_quantity=80,
                image_url="https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500"
            ),

            # === FASHION ===
            Product(
                name="White Casual Sneakers",
                description="Minimalist low-top lace-up shoes for daily wear.",
                category="Fashion",
                price=45.00,
                stock_quantity=40,
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"
            ),
            Product(
                name="Black Leather Wallet",
                description="Classic bi-fold wallet made from genuine leather with RFID blocking.",
                category="Fashion",
                price=24.99,
                stock_quantity=60,
                image_url="https://images.unsplash.com/photo-1627123424574-724758594e93?w=500"
            ),
            Product(
                name="Unisex Sunglasses",
                description="Classic dark lenses with lightweight UV400 protection frames.",
                category="Fashion",
                price=18.50,
                stock_quantity=75,
                image_url="https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500"
            ),
            Product(
                name="Canvas Backpack",
                description="Everyday travel laptop bag with adjustable shoulder straps.",
                category="Fashion",
                price=34.99,
                stock_quantity=30,
                image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"
            ),

            # === BOOKS ===
            Product(
                name="Notebook Journal",
                description="A5 hardcover lined notebook with thick paper for writing.",
                category="Books",
                price=8.99,
                stock_quantity=150,
                image_url="https://images.unsplash.com/photo-1512820790803-83ca734da794?w=500"
            ),
            Product(
                name="Fiction Novel",
                description="A gripping modern paperback drama and best-selling story book.",
                category="Books",
                price=14.95,
                stock_quantity=45,
                image_url="https://images.unsplash.com/photo-1495640388908-05fa85288e61?w=500"
            ),
            Product(
                name="Sci-Fi Paperback",
                description="An epic adventure book set in a futuristic universe.",
                category="Books",
                price=12.99,
                stock_quantity=35,
                image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"
            ),
            Product(
                name="Recipe Cook Book",
                description="Simple, quick 30-minute meals for healthy everyday cooking.",
                category="Books",
                price=19.99,
                stock_quantity=25,
                image_url="https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=500"
            ),

            # === HOME & KITCHEN ===
            Product(
                name="Ceramic Coffee Mug",
                description="12oz matte black microwave-safe coffee and tea mug.",
                category="Home & Kitchen",
                price=10.00,
                stock_quantity=90,
                image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500"
            ),
            Product(
                name="Stainless Steel Water Bottle",
                description="Vacuum insulated double-walled thermos flask to keep drinks cold.",
                category="Home & Kitchen",
                price=19.95,
                stock_quantity=110,
                image_url="https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500"
            ),
            Product(
                name="Scented Soy Candle",
                description="Lavender infused calming candle in an elegant glass jar.",
                category="Home & Kitchen",
                price=13.50,
                stock_quantity=55,
                image_url="https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500"
            ),
            Product(
                name="Non-Stick Frying Pan",
                description="8-inch aluminum skillet pan with heat-resistant handle.",
                category="Home & Kitchen",
                price=27.99,
                stock_quantity=40,
                image_url="https://images.unsplash.com/photo-1593113598332-cd288d649433?w=500"
            ),

            # === SPORTS ===
            Product(
                name="Yoga Mat",
                description="High-density non-slip exercise fitness mat with carrying strap.",
                category="Sports",
                price=22.00,
                stock_quantity=65,
                image_url="https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=500"
            ),
            Product(
                name="Size 7 Basketball",
                description="Durable rubber composite indoor/outdoor basketball.",
                category="Sports",
                price=24.99,
                stock_quantity=50,
                image_url="https://images.unsplash.com/photo-1519766304817-4f37bda74a27?w=500"
            ),
            Product(
                name="Skipping Rope",
                description="Adjustable speed jump rope for cardio conditioning workouts.",
                category="Sports",
                price=8.95,
                stock_quantity=120,
                image_url="https://images.unsplash.com/photo-1617083934555-ac7d4fee12a4?w=500"
            ),
            Product(
                name="Sports Water Jug",
                description="Large half-gallon leakproof bottle with time tracking markers.",
                category="Sports",
                price=16.99,
                stock_quantity=85,
                image_url="https://images.unsplash.com/photo-1523362628745-0c100150b504?w=500"
            )
        ]

        db.session.bulk_save_objects(simple_products)
        db.session.commit()
        print("------------------------------------------------------------")
        print(" SUCCESS: 20 Simple daily products seeded successfully!")
        print("------------------------------------------------------------")

if __name__ == "__main__":
    seed_database()