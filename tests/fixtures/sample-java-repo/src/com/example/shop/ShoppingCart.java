package com.example.shop;

import java.util.List;
import java.util.ArrayList;

/**
 * Manages the shopping cart for an e-commerce application.
 * Handles item additions, removals, and total calculations.
 */
public class ShoppingCart {

    private List<CartItem> items;
    private double discountPercentage;

    /**
     * Creates a new empty shopping cart.
     */
    public ShoppingCart() {
        this.items = new ArrayList<>();
        this.discountPercentage = 0.0;
    }

    /**
     * Adds an item to the cart. If the item already exists, increments quantity.
     */
    public void addItem(CartItem item) {
        for (CartItem existing : items) {
            if (existing.getProductId().equals(item.getProductId())) {
                existing.setQuantity(existing.getQuantity() + item.getQuantity());
                return;
            }
        }
        items.add(item);
    }

    /**
     * Removes an item from the cart by product ID.
     */
    public boolean removeItem(String productId) {
        return items.removeIf(item -> item.getProductId().equals(productId));
    }

    /**
     * Calculates the total price of all items in the cart,
     * applying any active discount.
     */
    public double calculateTotal() {
        double subtotal = 0.0;
        for (CartItem item : items) {
            subtotal += item.getPrice() * item.getQuantity();
        }

        if (discountPercentage > 0) {
            double discount = subtotal * (discountPercentage / 100.0);
            return subtotal - discount;
        }

        return subtotal;
    }

    /**
     * Applies a bulk discount based on the number of items.
     */
    public void applyBulkDiscount() {
        int totalQuantity = getTotalQuantity();

        if (totalQuantity >= 100) {
            this.discountPercentage = 15.0;
        } else if (totalQuantity >= 50) {
            this.discountPercentage = 10.0;
        } else if (totalQuantity >= 10) {
            this.discountPercentage = 5.0;
        }
    }

    /**
     * Returns the total number of items in the cart.
     */
    public int getTotalQuantity() {
        int total = 0;
        for (CartItem item : items) {
            total += item.getQuantity();
        }
        return total;
    }

    public List<CartItem> getItems() {
        return items;
    }

    public double getDiscountPercentage() {
        return discountPercentage;
    }
}
