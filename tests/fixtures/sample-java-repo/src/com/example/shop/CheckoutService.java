package com.example.shop;

/**
 * Service that processes checkout operations.
 * Validates the cart, applies discounts, and creates orders.
 */
public class CheckoutService {

    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    public CheckoutService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
    }

    /**
     * Processes a checkout operation for the given cart.
     * Validates the cart is not empty, applies bulk discounts,
     * processes payment, and saves the order.
     */
    public Order checkout(ShoppingCart cart, String customerId) {
        if (cart.getItems().isEmpty()) {
            throw new IllegalStateException("Cannot checkout an empty cart");
        }

        cart.applyBulkDiscount();
        double total = cart.calculateTotal();

        if (total <= 0) {
            throw new IllegalStateException("Cart total must be positive");
        }

        PaymentResult payment = paymentGateway.charge(customerId, total);

        if (payment.isSuccessful()) {
            Order order = new Order(customerId, cart.getItems(), total);
            orderRepository.save(order);
            return order;
        } else {
            throw new RuntimeException("Payment failed: " + payment.getErrorMessage());
        }
    }

    /**
     * Calculates a price preview without processing payment.
     */
    public double previewTotal(ShoppingCart cart) {
        cart.applyBulkDiscount();
        return cart.calculateTotal();
    }
}
