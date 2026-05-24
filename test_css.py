import streamlit as st
st.set_page_config(layout="wide")

st.markdown("""
<style>
/* Target the st.container() inner block */
div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) {
    position: relative;
    border: 1px solid rgba(203,213,225,0.7);
    border-radius: 14px;
    padding: 16px 12px;
    background: #ffffff;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);
}
div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card):hover {
    border-color: #3b82f6;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}
/* Stretch button over everything seamlessly */
div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) .stButton {
    position: absolute;
    top: 0; left: 0; bottom: 0; right: 0;
    margin: 0 !important;
    opacity: 0 !important;
    z-index: 10;
}
div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) .stButton button {
    width: 100%; height: 100%; cursor: pointer; padding: 0 !important; margin: 0 !important;
}

/* Base styles for the card internals */
.custom-school-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.custom-school-card img {
    height: 50px;
    width: 100%;
    object-fit: contain;
    margin-bottom: 12px;
}
.custom-school-title {
    font-size: 14px;
    font-weight: 700;
    color: #1e293b;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    with st.container():
        st.markdown('''
        <div class="custom-school-card">
            <div style="height:50px;width:50px;background:red;margin-bottom:12px;"></div>
            <div class="custom-school-title">School Name 1</div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("School Name 1", use_container_width=True):
            st.write("Clicked 1")

with c2:
    with st.container():
        st.markdown('''
        <div class="custom-school-card">
            <div style="height:50px;width:50px;background:blue;margin-bottom:12px;"></div>
            <div class="custom-school-title">School Name 2</div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("School Name 2", use_container_width=True):
            st.write("Clicked 2")
