import { motion } from 'motion/react';
import type { HTMLMotionProps } from 'motion/react';

const EASE = [0.22, 0.1, 0.36, 1] as const;

// Scroll-triggered fade-up with blur
export function FadeUp({
  delay = 0,
  duration = 0.5,
  className,
  children,
  ...props
}: HTMLMotionProps<'div'> & { delay?: number; duration?: number }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 22, filter: 'blur(6px)' }}
      whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration, delay, ease: EASE }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

// On-mount fade-up (for above-the-fold hero elements)
export function FadeIn({
  delay = 0,
  duration = 0.5,
  className,
  children,
  ...props
}: HTMLMotionProps<'div'> & { delay?: number; duration?: number }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20, filter: 'blur(6px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration, delay, ease: EASE }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

// Stagger container — children use staggerItemVariants
export const staggerContainer = (delayChildren = 0.05, staggerChildren = 0.08) => ({
  hidden: {},
  visible: { transition: { staggerChildren, delayChildren } },
});

export const staggerItem = {
  hidden: { opacity: 0, y: 20, filter: 'blur(5px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.45, ease: EASE },
  },
};

export function StaggerGroup({
  delayChildren = 0.05,
  staggerChildren = 0.08,
  className,
  children,
  ...props
}: HTMLMotionProps<'div'> & { delayChildren?: number; staggerChildren?: number }) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-60px' }}
      variants={staggerContainer(delayChildren, staggerChildren)}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  className,
  children,
  ...props
}: HTMLMotionProps<'div'>) {
  return (
    <motion.div className={className} variants={staggerItem} {...props}>
      {children}
    </motion.div>
  );
}
