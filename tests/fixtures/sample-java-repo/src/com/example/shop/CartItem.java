package com.example.shop;

/**
 * Represents a single item in the shopping cart.
 */
public class CartItem {

    private String productId;
    private String name;
    private double price;
    private int quantity;

    public CartItem(String productId, String name, double price, int quantity) {
        this.productId = productId;
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    public String getProductId() {
        return productId;
    }

    public String getName() {
        return name;
    }

    public double getPrice() {
        return price;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    @Override
    public String toString() {
        return name + " (x" + quantity + ") @ $" + price;
    }
}
