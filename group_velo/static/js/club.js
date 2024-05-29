function valueIsNbr(value) {
  const regex = /^\d+(\.\d+)?$/;
  return regex.test(value);
}

export function createRules() {
  Iodine.rule("upperGreaterThanLower", function (value, lowerValue) {
    if (!isNaN(lowerValue)) {
      return Number(value) > Number(lowerValue);
    }
    return true;
  });

  Iodine.rule("lowerLessThanUpper", function (value, upperValue) {
    if (!isNaN(upperValue)) {
      return Number(value) < Number(upperValue);
    }
    return true;
  });

  Iodine.setErrorMessage(
    "upperGreaterThanLower",
    "The upper pace range should be greater than the lower pace range.",
  );

  Iodine.setErrorMessage(
    "lowerLessThanUpper",
    "The lower pace range should be less than the upper pace range.",
  );
}

function getPartnerField(field, prefix) {
  const fieldPrefix = field.id.split("-")[0];
  const partnerId = fieldPrefix + prefix;
  const partnerField = document.getElementById(partnerId);
  return partnerField;
}

export function setRules() {
  const lowerPaceFields = document.querySelectorAll(".lower-pace-range-field");
  const upperPaceFields = document.querySelectorAll(".upper-pace-range-field");

  lowerPaceFields.forEach((field) => {
    const partnerField = getPartnerField(field, "-upper_pace_range");
    field.addEventListener("input", () => {
      if (valueIsNbr(field.value) && !isNaN(field.value)) {
        partnerField.setAttribute(
          "data-rules",
          `["numeric", "upperGreaterThanLower:${field.value}"]`,
        );
      }
    });
  });

  upperPaceFields.forEach((field) => {
    const partnerField = getPartnerField(field, "-lower_pace_range");
    field.addEventListener("input", () => {
      if (valueIsNbr(field.value) && !isNaN(field.value)) {
        partnerField.setAttribute(
          "data-rules",
          `["numeric", "lowerLessThanUpper:${field.value}"]`,
        );
      }
    });
  });
}
