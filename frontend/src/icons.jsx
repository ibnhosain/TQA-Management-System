/* ═══════════════ আইকন — ইমোজির বদলে আসল অ্যাপের মতো রেখা-আইকন ═══════════════
   পুরো অ্যাপে ইমোজি (✔ ⚠️ 📚 🎥 …) আইকন হিসেবে বসানো ছিল — দেখতে "AI-বানানো"
   লাগত, আর প্রতিটি ফোন/কম্পিউটারে আলাদা চেহারায় আসত। এখন একটিমাত্র নকশার
   আইকন-সেট (Lucide — পেশাদার অ্যাপে বহুল ব্যবহৃত) সব জায়গায়।

   কীভাবে: লেখায় ইমোজি যেমন আছে তেমনই থাকে; Btn, Tag, Section, Stat, Modal,
   টোস্ট আর মেনু withIcons() দিয়ে দেখানোর সময় চেনা ইমোজিকে আইকনে বদলে নেয়।
   ফলে শত শত জায়গা আলাদা করে বদলাতে হয়নি, আর WhatsApp-এর বার্তার লেখা
   (যেখানে ইমোজিই স্বাভাবিক) অক্ষত থাকে।
   ⚠️ <option>-এর ভেতরে SVG বসে না — সেখানে stripEmoji() ব্যবহার করুন।
   নতুন ইমোজি লিখলে এখানে মানচিত্রে যোগ করুন, নইলে ইমোজিই দেখাবে। */
import React, { Fragment } from "react";
import {
  AlarmClock, ArrowUpToLine, Ban, Banknote, Bell, BookMarked, BookOpen, Bookmark, Bot,
  CalendarCheck, CalendarDays, Camera, ChartColumn, Check, CircleCheck, CircleHelp, CircleX,
  ClipboardList, Clock, CreditCard, Crown, Dices, Download, Ear, Eye, EyeOff, FileText, Film,
  Folder, FolderOpen, Gift, Globe, GraduationCap, Hand, HandHeart, Heart, Hourglass, House,
  Image, Inbox, KeyRound, Landmark, Languages, LayoutDashboard, Library, Lightbulb, Link,
  Lock, LockOpen, Mail, MailOpen, Maximize, Medal, Megaphone, Menu, MessageCircle, MessagesSquare, Mic,
  Minus, Monitor, Moon, NotebookPen, Paperclip, Pause, PartyPopper, PenLine, Pencil, Phone,
  PhoneOff, Pin, Plus, Pointer, Presentation, Printer, Receipt, RefreshCw, Repeat, Rocket,
  Save, ScrollText, Search, Send, SendHorizontal, Settings, Shield, SkipForward, Smartphone,
  Smile, Sparkles, Speech, Sprout, Star, Tag, Target, Timer, Trash2, TreePalm, TrendingUp,
  TriangleAlert, Upload, User, UserRound, Users, Video, Wallet, Wrench, X, Zap, Layers,
  ShieldCheck, Clapperboard, Footprints, CalendarClock, BookCheck, IdCard, Undo2, Backpack,
} from "lucide-react";

/* Lucide-এ নেই এমন কয়েকটি — একই ধাঁচে (২৪×২৪, রেখা, গোল প্রান্ত) হাতে আঁকা */
const svgIcon = (paths) =>
  function CustomIcon({ size = 24, strokeWidth = 2, color = "currentColor", style, ...p }) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        style={style}
        {...p}
      >
        {paths.map((d, i) => (
          <path key={i} d={d} />
        ))}
      </svg>
    );
  };
export const Mosque = svgIcon([
  "M3 21h18",
  "M4 21V11l1-2 1 2v10",
  "M18 21V11l1-2 1 2v10",
  "M8 21v-7h8v7",
  "M8 14c0-2.5 1.8-4 4-5.5 2.2 1.5 4 3 4 5.5",
  "M12 8.5V6",
  "M11 21v-3a1 1 0 0 1 2 0v3",
]);
export const Lantern = svgIcon([
  "M12 2v2",
  "M10 4h4l2 3H8z",
  "M8.5 7h7v10h-7z",
  "M8 17h8l-1 3H9z",
  "M12 10.5c.8.9 1 1.6 1 2.2a1 1 0 0 1-2 0c0-.6.2-1.3 1-2.2z",
]);
export const Kaaba = svgIcon([
  "M4 8l8-4 8 4v9l-8 4-8-4z",
  "M4 8l8 4 8-4",
  "M12 12v9",
  "M4 10.5l8 4 8-4",
]);

// রঙিন অবস্থা-বিন্দু (🟢 🔴 …) — আইকন নয়, ছোট ভরাট বৃত্ত
const dot = (fill) =>
  function Dot({ size = 24, style }) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" style={style} aria-hidden="true">
        <circle cx="12" cy="12" r="6" fill={fill} />
      </svg>
    );
  };

/* ইমোজি → আইকন। চাবিতে U+FE0F (ইমোজি-ভ্যারিয়েশন) রাখা হয়নি — মেলানোর সময়
   ঐচ্ছিক ধরা হয়, তাই "⚠" ও "⚠️" দুটোই মেলে। তীর (→ ←) আর রেটিংয়ের ★
   ইচ্ছা করেই বাদ — ওগুলো টাইপোগ্রাফির চিহ্ন, ইমোজি নয়। */
export const EMOJI_ICON = {
  "✔": Check, "✓": Check, "✅": CircleCheck, "✘": X, "✕": X, "❌": CircleX,
  "⚠": TriangleAlert, "⏳": Hourglass, "✏": Pencil, "✎": Pencil, "📋": ClipboardList,
  "🔄": RefreshCw, "🔁": Repeat, "📚": Library, "🗑": Trash2, "📖": BookOpen,
  "💬": MessageCircle, "🎥": Video, "➕": Plus, "➖": Minus, "📲": Smartphone, "🌟": Star,
  "⭐": Star, "📤": SendHorizontal, "🖨": Printer, "⛔": Ban, "📷": Camera, "💾": Save,
  "📨": Inbox, "📌": Pin, "🕐": Clock, "⏰": AlarmClock, "⏱": Timer, "⬇": Download,
  "⬆": Upload, "🧾": Receipt, "🎓": GraduationCap, "📅": CalendarDays, "🗓": CalendarCheck,
  "↩": Undo2, "✍": PenLine, "🤲": HandHeart, "👥": Users, "👤": User, "🔗": Link,
  "🔔": Bell, "💡": Lightbulb, "🔍": Search, "📈": TrendingUp, "📊": ChartColumn,
  "💳": CreditCard, "💵": Banknote, "💰": Wallet, "✨": Sparkles, "📜": ScrollText,
  "⚡": Zap, "👳": UserRound, "🧕": UserRound, "🧒": Smile, "🧑‍🏫": Presentation,
  "👨‍🏫": Presentation, "📄": FileText, "🖼": Image, "🔒": Lock, "🔓": LockOpen, "🔑": KeyRound,
  "📱": Smartphone, "📝": NotebookPen, "📥": Download, "📗": BookMarked, "📘": BookMarked,
  "👁": Eye, "🙈": EyeOff, "🌱": Sprout, "🏦": Landmark, "🕌": Mosque, "🕋": Kaaba,
  "🌙": Moon, "⚙": Settings, "🖥": Monitor, "🛠": Wrench, "🔧": Wrench, "🎲": Dices,
  "📁": Folder, "🗂": FolderOpen, "🎁": Gift, "📧": Mail, "✉": Mail, "📭": MailOpen,
  "✋": Hand, "👋": Hand, "🌍": Globe, "📞": Phone, "📵": PhoneOff, "🔤": Languages,
  "🏮": Lantern, "🪔": Lantern, "📢": Megaphone, "🏝": TreePalm, "🗣": Speech, "☰": Menu,
  "🔝": ArrowUpToLine, "🏠": House, "👑": Crown, "🛡": Shield, "🤔": CircleHelp,
  "❓": CircleHelp, "🤖": Bot, "📎": Paperclip, "❤": Heart, "🔖": Bookmark, "🪵": Layers,
  "👆": Pointer, "🚀": Rocket, "🏷": Tag, "👂": Ear, "🎤": Mic, "⏸": Pause, "🎯": Target,
  "⏭": SkipForward, "🏅": Medal, "🎉": PartyPopper, "⛶": Maximize, "🎞": Film,
  "🐪": Footprints, "🎒": Backpack,
  "🟢": dot("#16a34a"), "🔴": dot("#dc2626"), "🟠": dot("#ea580c"), "🟡": dot("#eab308"),
  "⚪": dot("#d1d5db"),
};

/* মেনুর আইকন — পাতার id অনুযায়ী (ইমোজির চেয়ে অর্থ স্পষ্ট করে বাছা) */
export const NAV_ICON = {
  overview: LayoutDashboard, classes: Video, instantclass: Zap, postponed: CalendarClock,
  routine: CalendarDays, lectures: ClipboardList, settings: Settings,
  syllabus: ScrollText, attendance: CalendarCheck, assignments: NotebookPen, homework: BookCheck,
  exams: Medal, progress: TrendingUp, payments: CreditCard, studentpayments: Banknote,
  waoutbox: MessagesSquare, teacherreport: Star, coursemgr: BookOpen, allstudents: Users,
  allteachers: Presentation, loginsend: IdCard, amal: Moon, admissions: GraduationCap,
  trials: Sprout, accounts: Landmark, forms: Inbox, books: Library, library: Lantern,
  salah: Mosque, myreceipts: Receipt, leaves: Mail, notices: Pin, manage: Wrench,
  decks: Clapperboard, approvalsDeck: ShieldCheck, lecturesStudent: BookMarked,
};

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const KEYS = Object.keys(EMOJI_ICON).sort((a, b) => b.length - a.length);
const PATTERN = `(${KEYS.map(esc).join("|")})\\uFE0F?`;
const HAS = new RegExp(PATTERN, "u");

/* একটি আইকন — লেখার আকারের সাথে বাড়ে-কমে (em), রং লেখার রং */
export function Ico({ as: Comp, e, size = "1.15em", strokeWidth = 2.1, style, ...p }) {
  const C = Comp || EMOJI_ICON[String(e || "").replace(/️/g, "")];
  if (!C) return e || null;
  return (
    <C
      size={size}
      strokeWidth={strokeWidth}
      aria-hidden="true"
      style={{ verticalAlign: "-0.2em", flexShrink: 0, ...style }}
      {...p}
    />
  );
}

/* লেখা/children-এর ভেতরের চেনা ইমোজি → আইকন। অচেনা কিছু হলে যেমন ছিল তেমন। */
export function withIcons(node, props) {
  if (typeof node === "string") {
    if (!HAS.test(node)) return node;
    const re = new RegExp(PATTERN, "gu");
    const out = [];
    let last = 0;
    let m;
    while ((m = re.exec(node))) {
      if (m.index > last) out.push(node.slice(last, m.index));
      out.push(<Ico key={`i${m.index}`} e={m[1]} {...props} />);
      last = m.index + m[0].length;
    }
    if (last < node.length) out.push(node.slice(last));
    return out;
  }
  if (Array.isArray(node))
    return node.map((n, i) => {
      const r = withIcons(n, props);
      return Array.isArray(r) ? <Fragment key={`f${i}`}>{r}</Fragment> : r;
    });
  return node;
}

/* <option> বা title-এর মতো জায়গায় (যেখানে SVG বসে না) — চেনা ইমোজি মুছে দেয় */
export const stripEmoji = (s) =>
  typeof s === "string" ? s.replace(new RegExp(PATTERN + "\\s*", "gu"), "").trim() : s;
