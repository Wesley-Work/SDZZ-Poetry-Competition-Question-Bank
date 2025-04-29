// 内容转成下划线
const sentencesToUnderline = (content: string) => {
  return content.replace(/[\u4e00-\u9fa5+]/g, '__');
};

// 短句切割
const sentencesSlice = (content: string, isNext: boolean) => {
  const chineseReg = /([\u4e00-\u9fa5]+)/g;
  const markReg = /([。！，？])/g;
  // 分割，获取标点符号
  const mark = content.match(markReg);
  const sentences = content.match(chineseReg);

  if (!sentences || !mark || sentences.length < 2 || mark.length < 2) {
    return undefined;
  }

  const [firstSentence, secondSentence] = sentences;
  const [firstMark, secondMark] = mark;

  let question, answer;
  if (isNext) {
    // isNext 为 true，则第二句为问题，第一句为答案
    question = `${sentencesToUnderline(firstSentence)}${firstMark}${secondSentence}${secondMark}`;
    answer = `${firstSentence}${firstMark}`;
  } else {
    // isNext 为 false，则第一句为问题，第二句为答案
    question = `${firstSentence}${firstMark}${sentencesToUnderline(secondSentence)}`;
    answer = `${secondSentence}${secondMark}`;
  }

  return {
    mode: 'sentences',
    question,
    answer,
    isNext,
  };
};

// 整首切割
const wholePoemSlice = (content: string, isNext: boolean, canCross: boolean) => {
  const chineseReg = /([\u4e00-\u9fa5]+)/g;
  const markReg = /([。！，？])/g;
  // 分割，获取标点符号
  const mark = content.match(markReg);
  const sentences = content.match(chineseReg);

  if (!sentences || !mark) {
    return undefined;
  }

  let randomKey = Math.floor(Math.random() * sentences.length);
  let isNextConst = isNext;

  // 如果isNext为true，但是canCross为false，即答案为下一句但是不能跨句，则强制randomKey-1，isNextConst为false
  if (isNext && !canCross) {
    randomKey = randomKey - 1;
    isNextConst = false;
  }
  // 如果isNext为false，但是canCross为false，即答案为上一句但是不能跨句，则强制randomKey+1，isNextConst为true
  if (!isNext && !canCross) {
    randomKey = randomKey + 1;
    isNextConst = true;
  }

  const [firstSentence, secondSentence] = sentences;
  const [firstMark, secondMark] = mark;

  let question, answer;
  if (isNext) {
    // isNext 为 true，则第二句为问题，第一句为答案
    question = `${secondSentence}${secondMark}${sentencesToUnderline(firstSentence)}`;
    answer = `${firstSentence}${firstMark}`;
  } else {
    // isNext 为 false，则第一句为问题，第二句为答案
    question = `${firstSentence}${firstMark}${sentencesToUnderline(secondSentence)}`;
    answer = `${secondSentence}${secondMark}`;
  }

  return {
    mode: 'whole',
    question,
    answer,
    isNext: isNextConst,
  };
};

/**
 * 诗词句切割
 * @param content 诗词内容
 * @param isNext 是否抽下一句
 * @param canCross 是否跨句
 * @param isWhole 是否抽的是整首
 * @returns string
 */
export const poemSlice = (content: string, isNext: boolean, canCross: boolean, isWhole: boolean) => {
  return isWhole ? wholePoemSlice(content, isNext, canCross) : sentencesSlice(content, isNext);
};
