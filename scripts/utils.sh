#!/bin/bash

#######################################################################
# This script provides reusable utility functions for colored terminal
# output. You can extend or import this master utils script into any
# other shell script to reuse the color-printing functions.
#
# How to extend this script in another script:
#   source /path/to/utils.sh
#   printInfoText "Your message"
#######################################################################

# -------------------------------------------------------------
# Color Variables
# -------------------------------------------------------------
COLOR_ERROR_TEXT="\033[31m" # red
COLOR_WARNING_TEXT="\033[33m"   # yellow
COLOR_INFO_TEXT="\033[36m"  # blue
COLOR_SUCCESS_TEXT="\033[32m"   # green


resetTextColor() {
    # -------------------------------------------------------------
    # resetTextColor
    # Description: Resets terminal text color back to default.
    # Arguments: None
    # Output: None
    # -------------------------------------------------------------

    echo -e "\033[0m"
}


printErrorText() {
    # -------------------------------------------------------------
    # printErrorText
    # Description: Prints error text in red.
    # Arguments: $1 → string text to print
    # Output: Colored text
    # -------------------------------------------------------------

    echo -e "${COLOR_ERROR_TEXT}$1"
    resetTextColor
}


printWarningText() {
    # -------------------------------------------------------------
    # printWarningText
    # Description: Prints warning text in yellow.
    # Arguments: $1 → string text to print
    # Output: Colored text
    # -------------------------------------------------------------

    echo -e "${COLOR_WARNING_TEXT}$1"
    resetTextColor
}


printInfoText() {
    # -------------------------------------------------------------
    # printInfoText
    # Description: Prints info text in cyan.
    # Arguments: $1 → string text to print
    # Output: Colored text
    # -------------------------------------------------------------

    echo -e "${COLOR_INFO_TEXT}$1"
    resetTextColor
}


printSuccessText() {
    # -------------------------------------------------------------
    # printSuccessText
    # Description: Prints success text in green.
    # Arguments: $1 → string text to print
    # Output: Colored text
    # -------------------------------------------------------------

    echo -e "${COLOR_SUCCESS_TEXT}$1"
    resetTextColor
}
