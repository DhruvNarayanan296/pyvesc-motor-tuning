import streamlit as st
import serial
import pyvesc
from pyvesc import SetRPM, SetCurrent, SetRotorPositionMode
import threading
import time

# Configuration
SERIAL_PORT = 'COM3'
BAUDRATE = 115200

# Initialize global variables
ser = None
rpm_thread = None
rpm_thread_running = False

def init_serial_connection():
    global ser
    if ser is None:
        try:
            ser = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE, timeout=0.05)
            print('COM3 is open:', ser.is_open)
        except serial.SerialException as e:
            st.error(f"Failed to open serial port {SERIAL_PORT}: {e}")
            ser = None
    else:
        if not ser.is_open:
            try:
                ser.open()
                print('COM3 is open:', ser.is_open)
            except serial.SerialException as e:
                st.error(f"Failed to open serial port {SERIAL_PORT}: {e}")

def close_serial_connection():
    global ser
    if ser is not None and ser.is_open:
        try:
            ser.close()
            print('COM3 is closed:', ser.is_open)
        except serial.SerialException as e:
            st.error(f"Failed to close serial port {SERIAL_PORT}: {e}")

def start_motor(rpm, duty_cycle):
    global rpm_thread, rpm_thread_running
    try:
        init_serial_connection()
        if ser is not None and ser.is_open:
            ser.write(pyvesc.encode(SetRotorPositionMode(SetRotorPositionMode.DISP_POS_MODE_ENCODER)))
            # Set the RPM and Duty Cycle
            ser.write(pyvesc.encode(SetRPM(rpm)))
            # Example: Adjust duty cycle (this will depend on how your VESC handles duty cycle settings)
            # You might need to use a different VESC command if it supports duty cycle directly.
            # For now, we will use RPM as a placeholder for duty cycle.
            ser.write(pyvesc.encode(SetCurrent(duty_cycle)))

            st.session_state.motor_running = True
            st.session_state.current_rpm = rpm
            st.session_state.current_duty_cycle = duty_cycle
            st.success(f"Motor started at {rpm} RPM with duty cycle {duty_cycle}")

            if rpm_thread is None or not rpm_thread.is_alive():
                rpm_thread_running = True
                rpm_thread = threading.Thread(target=continuous_rpm_update, args=(rpm,))
                rpm_thread.start()
        else:
            st.error("Serial port is not open. Please check the connection.")
    except Exception as e:
        st.error(f"Error starting motor: {e}")

def stop_motor():
    global rpm_thread_running
    try:
        init_serial_connection()
        if ser is not None and ser.is_open:
            ser.write(pyvesc.encode(SetCurrent(0)))
            st.session_state.motor_running = False
            st.session_state.current_rpm = None
            st.session_state.current_duty_cycle = None
            st.success("Motor stopped")
        else:
            st.error("Serial port is not open. Please check the connection.")
    except Exception as e:
        st.error(f"Error stopping motor: {e}")
    finally:
        rpm_thread_running = False
        close_serial_connection()

def continuous_rpm_update(rpm):
    while rpm_thread_running:
        try:
            init_serial_connection()
            if ser is not None and ser.is_open:
                ser.write(pyvesc.encode(SetRPM(rpm)))
                time.sleep(0.1)  # Adjust this delay as needed
            else:
                st.error("Serial port is not open. Stopping RPM updates.")
                break
        except Exception as e:
            st.error(f"Error updating RPM: {e}")
            break

def main():
    st.title("Torus Robotics")
    st.write("Motor Tuning with VESC.")

    if 'motor_running' not in st.session_state:
        st.session_state.motor_running = False
    if 'current_rpm' not in st.session_state:
        st.session_state.current_rpm = None
    if 'current_duty_cycle' not in st.session_state:
        st.session_state.current_duty_cycle = None

    rpm = st.number_input("Enter RPM", min_value=0, max_value=100000, step=100, value=10000)
    duty_cycle = st.number_input("Enter Duty Cycle (%)", min_value=0, max_value=100, step=1, value=50)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Motor"):
            start_motor(rpm, duty_cycle)

    with col2:
        if st.button("Stop Motor"):
            stop_motor()

    if st.session_state.motor_running:
        st.write(f"Motor is running at {st.session_state.current_rpm} RPM with duty cycle {st.session_state.current_duty_cycle}%.")
    else:
        st.write("Motor is stopped.")

if __name__ == "__main__":
    try:
        main()
    finally:
        close_serial_connection()
