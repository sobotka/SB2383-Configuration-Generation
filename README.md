# **Who**
If you have to ask, this probably isn't ready for you.

If you don't have to ask, the following will provide insight.

# **How**

```
usage: generate_config.py [-h] [-et EXPONENT_TOE] [-ps EXPONENT_SHOULDER] [-fs FULCRUM_SLOPE] [-fi FULCRUM_INPUT] [-fo FULCRUM_OUTPUT] [-ll LIMIT_LOW] [-lh LIMIT_HIGH] [-pi PRIMARIES_INSET PRIMARIES_INSET PRIMARIES_INSET] [-pr PRIMARIES_ROTATE PRIMARIES_ROTATE PRIMARIES_ROTATE]
```
All of the following creative options will influence what you end up seeing in terms of hue, value, and chroma.

### **-h, --help**
Shows help.

### **-et EXPONENT_TOE, --exponent_toe EXPONENT_TOE**
Set toe curve rate of change as an exponential power, hello Sean Cooper (default: 1.5)

#### **Description**
This will set the rate of change of the primary image formation curve as applied to the interstitial log encoding applied toward the lower end of the log2 encoding. Higher values tension the curve toward the `y = 0.0` line, making the rate of change transition more abrupt.

#### **Visual Impact**
Will have an impact on rate of change of hue toward the lower end.

### **-ps EXPONENT_SHOULDER, --exponent_shoulder EXPONENT_SHOULDER**
Set shoulder curve rate of change as an exponential power (default: 1.5)

#### **Description**
This will set the rate of change of the primary image formation curve as applied to the interstitial log encoding applied toward the lower end of the log2 encoding. Higher values tension the curve toward the `y = 1.0` line, making the rate of change transition more abrupt.

#### **Visual Impact**
Will have an impact on rate of change of hue toward the upper end.

### **-fs FULCRUM_SLOPE, --fulcrum_slope FULCRUM_SLOPE**
Set central section rate of change as rise over run slope (default: 2.4)

#### **Description**
This controls the slope at the fulcrum region of the curve. Higher values make the rate of change in terms of rise over run more agressive.

#### **Visual Impact**
Influences rate of change on chroma, and hue flight.

### **-fi FULCRUM_INPUT, --fulcrum_input FULCRUM_INPUT**
Input fulcrum point relative to the normalized log2 range (default: 0.606060606061)

#### **Description**
The input value relative to the interstitial log2 encoding range. Given an achromatic sweep of values, input "middle grey".

#### **Visual Impact**
Influences value mapped to "middle grey" in relation to the output value.

### **-fo FULCRUM_OUTPUT, --fulcrum_output FULCRUM_OUTPUT**
Output fulcrum point relative to the normalized log2 range (default: 0.4586564468643811)

#### **Description**
The output value relative to the interstitial log2 encoding range. Given an achromatic sweep of values, output "middle grey".

#### **Visual Impact**
Influences value mapped to "middle grey" in relation to the input value.

### **-ll LIMIT_LOW, --limit_low LIMIT_LOW**
Lowest value of the normalized log2 range (default: -10.0)

#### **Description**
Given a range of open domain tristimulus values, the lowest ratio value accepted, expressed in normalized log2.

#### **Visual Impact**
In relation to the upper boundary value, determines the total ratio magnitude. Larger overall ranges increase density and may result in over-compression, and possibly posterization relative to the quantisation range of the output medium. Too large ranges may also yield an "uncanny" picture.

### **-lh LIMIT_HIGH, --limit_high LIMIT_HIGH**
Highest value of the normalized log2 range (default: 6.5)

#### **Description**
Given a range of open domain tristimulus values, the highest ratio value accepted, expressed in normalized log2.

#### **Visual Impact**
In relation to the lower boundary value, determines the total ratio magnitude. Larger overall ranges increase density and may result in over-compression, and possibly posterization relative to the quantisation range of the output medium. Too large ranges may also yield an "uncanny" picture.

### **-pi PRIMARIES_INSET PRIMARIES_INSET PRIMARIES_INSET, --primaries_inset PRIMARIES_INSET PRIMARIES_INSET PRIMARIES_INSET**
Percentage of scaling inset for the primaries (default: [0.15, 0.15, 0.1])

#### **Description**
Three values that dictate how much each "primary" is inset relative to the specified working space.

#### **Visual Impact**
Primarily influences the chromatic attenuation / amplification. Higher values toward one will yield more rapid attenuation of chroma, while lower values will relax, potentially to the point of posterization and picture breakup.

### **-pr PRIMARIES_ROTATE PRIMARIES_ROTATE PRIMARIES_ROTATE, --primaries_rotate PRIMARIES_ROTATE PRIMARIES_ROTATE PRIMARIES_ROTATE**
Rotational adjustment in degrees for each of the RGB primaries, positive counterclockwise, negative clockwise (default: [1.75, -0.5, -1.0])

#### **Description**
Three values that dictate how much each "primary" is rotated in relation to the resulting working space.

#### **Visual Impact**
Primarily influences the flight of hue toward compliments, and the rate at which the hues traverse.

### **-ao ACHROMATIC_OUTSET, --achromatic_outset ACHROMATIC_OUTSET**
Adjusts the achromatic centroid for all R=G=B tristimulus values as a decimal percentage. (default: 0.00)
#### **Description**
The amount to shift the white point toward the bisection line of the hull and the desired angle.
#### **Visual Impact**
Applies a general tint to the achromatic axis flight toward white. Also impacts the rate of change and flight of all hues.

### **-ar ACHROMATIC_ROTATE, --achromatic_rotate ACHROMATIC_ROTATE**
Adjusts the rotational angle of the achromatic centroid white point. Zero degrees is due north on the CIE chromaticity diagram. Positive values will rotate counterclockwise, negative values clockwise. (default: 0.0)
#### **Description**
The amount to rotate, in degrees, about the achromatic centroid toward the hull. The result shifts the achromatic centroid to the new position.
#### **Visual Impact**
Controls the general hue of the achromatic centroid on its flight toward white, moving the hue to the achromatic position selected in conjunction with the achromatic outset value. Also impacts the rate of change and flight of all hues.

### **-aa ACHROMATIC_ADAPTATION, --achromatic_adaptation ACHROMATIC_ADAPTATION**
Whether to re-align the achromatic centroid or leave the tristimulus values as-is. (default: True)
#### **Description**
Will leave the achromatic centroid off axis when used in conjunction with the achromatic rotate and achromatic outset above.
#### **Visual Impact**
Will create an imbalance in the achromatic centroid, leaving a tinted result in achromatic values for the flight to white. Will also result in invalid output domain values, yielding clip distortions.