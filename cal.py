import streamlit as st

# Set page configuration
st.set_page_config(page_title="Simple Calculator", page_icon="🔢", layout="centered")

# Title
st.title("🔢 Simple Calculator")
st.markdown("---")

# Create two columns for input
col1, col2 = st.columns(2)

with col1:
    num1 = st.number_input("Enter first number:", value=0.0, format="%.2f")

with col2:
    num2 = st.number_input("Enter second number:", value=0.0, format="%.2f")

# Operation selection
operation = st.selectbox(
    "Select operation:",
    ["➕ Addition", "➖ Subtraction", "✖ Multiplication", "➗ Division", "📐 Power", "√ Square Root"]
)

# Calculate button
if st.button("Calculate", type="primary", use_container_width=True):
    result = None
    error = None
    
    try:
        if operation == "➕ Addition":
            result = num1 + num2
            st.success(f"Result: {num1} + {num2} = {result}")
            
        elif operation == "➖ Subtraction":
            result = num1 - num2
            st.success(f"Result: {num1} - {num2} = {result}")
            
        elif operation == "✖ Multiplication":
            result = num1 * num2
            st.success(f"Result: {num1} × {num2} = {result}")
            
        elif operation == "➗ Division":
            if num2 == 0:
                st.error("❌ Error: Cannot divide by zero!")
            else:
                result = num1 / num2
                st.success(f"Result: {num1} ÷ {num2} = {result}")
                
        elif operation == "📐 Power":
            result = num1 ** num2
            st.success(f"Result: {num1} ^ {num2} = {result}")
            
        elif operation == "√ Square Root":
            if num1 < 0:
                st.error("❌ Error: Cannot calculate square root of negative number!")
            else:
                result = num1 ** 0.5
                st.success(f"Result: √{num1} = {result}")
                st.info(f"ℹ Note: Second number is ignored for square root operation")
                
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤ using Streamlit")
