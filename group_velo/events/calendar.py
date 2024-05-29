import calendar
import datetime
from calendar import HTMLCalendar

from django.urls import reverse

from group_velo.utils.utils import binary_search


class _localized_month:
    _months = [datetime.date(2001, i + 1, 1).strftime for i in range(12)]
    _months.insert(0, lambda x: "")

    def __init__(self, format):
        self.format = format

    def __getitem__(self, i):
        funcs = self._months[i]
        if isinstance(i, slice):
            return [f(self.format) for f in funcs]
        else:
            return funcs(self.format)

    def __len__(self):
        return 13


class _localized_day:
    # January 1, 2001, was a Monday.
    _days = [datetime.date(2001, 1, i + 1).strftime for i in range(7)]

    def __init__(self, format):
        self.format = format

    def __getitem__(self, i):
        funcs = self._days[i]
        if isinstance(i, slice):
            return [f(self.format) for f in funcs]
        else:
            return funcs(self.format)

    def __len__(self):
        return 7


day_name = _localized_day("%A")
day_abbr = _localized_day("%a")

month_name = _localized_month("%B")
month_abbr = _localized_month("%b")


class HighlightedCalendar(HTMLCalendar):
    def __init__(
        self,
        theyear,
        themonth,
        prevdate,
        nextdate,
        request,
        highlight=[],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.highlight_date = [x["ride_date"] for x in highlight]
        self.highlight_id = [x["ride_id"] for x in highlight]
        self.highlight_description = [x["ride_description"] for x in highlight]

        self.theyear = theyear
        self.themonth = themonth
        self.prevdate = prevdate
        self.nextdate = nextdate
        self.lastday = calendar.monthrange(self.theyear, self.themonth)[1]
        self.request = request

    def construct_query_params(self):
        qs = ""
        for param, value in self.request.GET.items():
            if param not in ["month", "year", "day"] and value:
                qs += f"&{param}={value}"
        return qs

    def get_new_date(self, y, fd, ld, weekday):
        today = datetime.date(self.theyear, self.themonth, 1)
        if y == "t" and fd - weekday > 0:
            return today.replace(day=1) - datetime.timedelta(days=(fd - weekday))
        if y == "b" and weekday - ld > 0:
            return today.replace(day=self.lastday) + datetime.timedelta(days=(weekday - ld))
        return None

    def formatweekheader(self):
        s = "".join(self.formatweekday(i) for i in self.iterweekdays())
        return f'<tr class="text-gray-500 dark:text-gray-300">{s}</tr>'

    def formatweekday(self, day):
        head_classes = ["font-light"]
        for cl in head_classes:
            if cl not in self.cssclasses_weekday_head[day]:
                self.cssclasses_weekday_head[day] += f" {cl}"
        return f'<th class="{self.cssclasses_weekday_head[day]}">{day_abbr[day][0]}</th>'

    def formatmonth(self, withyear=True):
        v = []
        a = v.append
        self.cssclass_month += " bg-transparent text-sm"

        a(f'<table border="0" cellpadding="0" cellspacing="0" class="justify-center {self.cssclass_month}">')
        a("\n")
        a("<thead>")
        a(self.formatmonthname(self.theyear, self.themonth, withyear=withyear))
        a("\n")
        a(self.formatweekheader())
        a("</thead>")
        a("\n")

        monthdays2cal = self.monthdays2calendar(self.theyear, self.themonth)
        a(
            '<tbody class="divide-y overflow-hidden divide-gray-200 dark:divide-gray-600 text-gray-700 '
            'dark:text-gray-200 rounded-lg">'
        )
        for i, week in enumerate(monthdays2cal):
            y = "t" if i == 0 else "b" if i == len(monthdays2cal) - 1 else ""
            a(self.formatweek(week, y=y))
            a("\n")
        a("</tbody>")
        a("</table>")
        a("\n")
        return "".join(v)

    def formatmonthname(self, theyear, themonth, withyear=True):
        head_classes = ["text-lg", "font-normal", "text-gray-700", "dark:text-gray-200"]
        for cl in head_classes:
            if cl not in self.cssclass_month_head:
                self.cssclass_month_head += f" {cl}"
        s = f"{month_name[themonth]} {theyear}" if withyear else f"{month_name[themonth]}"

        qs = self.construct_query_params()

        if self.prevdate:
            prev_url = self.request.path_info + f"?month={self.prevdate[0]}&year={self.prevdate[1]}" + qs
            prev_button = (
                f'<th><a href="{prev_url}">'
                '<span class="text-gray-500 text-2xl hover:text-gray-700 hover:text-bold">'
                "&lsaquo;</span></a></th>"
            )
        else:
            prev_button = '<th><span class="text-gray-300 text-2xl">&lsaquo;</span></th>'

        if self.nextdate:
            next_url = self.request.path_info + f"?month={self.nextdate[0]}&year={self.nextdate[1]}" + qs
            next_button = (
                f'<th><a href="{next_url}">'
                '<span class="text-gray-500 text-2xl hover:text-gray-700 hover:text-bold">'
                "&rsaquo;</span></a></th>"
            )
        else:
            next_button = '<th><span class="text-gray-300 text-2xl">&rsaquo;</span></th>'

        return (
            f"<tr>{prev_button}" f'<th colspan="5" class="{self.cssclass_month_head}">{s}</th>' f"{next_button}</tr>"
        )

    def day_cell_is_selected_date(self, day):
        selected_year = self.request.GET.get("year", None)
        selected_month = self.request.GET.get("month", None)
        selected_day = self.request.GET.get("day", None)

        if selected_year and selected_month and selected_day:
            if (
                int(selected_year) == self.theyear
                and int(selected_month) == self.themonth
                and int(selected_day) == day
            ):
                return True
        return False

    def formatday(self, day, weekday, y="", x="", fd=0, ld=6):
        # tailwind hack since variable class names are used in the method below. Listing the full class names used:
        # rounded-tl-lg rounded-tr-lg rounded-bl-lg rounded-br-lg border-l border-r border-t border-b
        # rounded-t-lg rounded-b-lg
        corner_class, rounded_class, edge_class, today_bg = "", "", "", ""
        weekday_classes = ["p-4", "text-center"]
        TODAY = datetime.datetime.date(datetime.datetime.today())
        hover_bg = " hover:bg-blue-100 dark:hover:bg-blue-300"

        qs = self.construct_query_params()
        cell_url = self.request.path_info + f"?year={self.theyear}&month={self.themonth}&day={day}" + qs
        selected_cell_url = self.request.path_info + f"{'?' if qs else ''}" + qs

        if day > 0 and datetime.date(self.theyear, self.themonth, day) == TODAY:
            today_bg = " bg-orange-200 dark:bg-orange-700"

        if x and y:
            rounded_class = f" rounded-{y}{x}-lg"
            corner_class = f" border-{x} border-{y} border-gray-200 dark:border-gray-500{rounded_class}"
        elif x is not y:
            edge_class = f" border-{x or y} border-gray-200 dark:border-gray-500"

        for cl in weekday_classes:
            if cl not in self.cssclasses[weekday]:
                self.cssclasses[weekday] += f" {cl}"

        # today's square
        if self.day_cell_is_selected_date(day):
            return (
                f'<td class="hover:cursor-pointer bg-blue-300 {rounded_class}"><a href="{selected_cell_url}">'
                f'<div class="{self.cssclasses[weekday]}{corner_class}{edge_class} '
                f'relative z-0 justify-center">{day}'
                f'<div class="absolute inset-0 ml-2.5 mt-2.5 flex z-10 bg-blue-600 rounded-full '
                f'w-[31px] h-[31px] shadow">'
                f'<div class="p-4 absolute inset-0 flex justify-center items-center z-20 text-white '
                f'font-normal">{day}</div></div></div></a></td>'
            )

        # highlighted square (ride exists)
        elif day in self.highlight_date:
            return (
                f'<td class="hover:cursor-pointer{today_bg}{hover_bg}{rounded_class}"><a href="{cell_url}">'
                f'<div class="{self.cssclasses[weekday]}{corner_class}{edge_class} '
                f'relative z-0 justify-center">{day}'
                f'<div class="absolute inset-0 ml-2.5 mt-2.5 flex z-10 bg-blue-600 rounded-full w-[31px] h-[31px] '
                f'shadow-lg">'
                f'<div class="p-4 absolute inset-0 flex justify-center items-center z-20 text-white font-normal">'
                f"{day}</div></div></div></a></td>"
            )

        # date outside the current month
        elif day == 0:
            new_date = self.get_new_date(y, fd, ld, weekday)
            day = new_date.day if new_date else day

            return (
                f'<td class="{rounded_class} add-a-ride"> '
                f'<div class="{self.cssclasses[weekday]}{corner_class}{edge_class} '
                f'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-100 z-10">{day}'
                f"</div></td>"
            )

        # day is in the past
        elif datetime.date(self.theyear, self.themonth, day) < TODAY:
            return (
                f'<td class="{today_bg}{rounded_class} add-a-ride align-middle">'
                f'<div class="{self.cssclasses[weekday]}{corner_class}{edge_class} '
                f'relative z-0 justify-center group">{day}'
                "</div></div></a></td>"
            )

        # normal calendar entry
        else:
            new_ride_url = reverse("events:create_event") + f"?year={self.theyear}&month={self.themonth}&day={day}"
            return (
                f'<td class="{today_bg}{rounded_class} add-a-ride align-middle">'
                f'<div class="{self.cssclasses[weekday]}{corner_class}{edge_class} '
                f'relative z-0 justify-center group">{day}'
                f'<a href="{new_ride_url}"><div class="absolute inset-0 ml-2.5 mt-2.5 z-10 bg-green-600 '
                "rounded-full w-[31px] h-[31px] shadow-lg opacity-0 group-hover:opacity-100 "
                'cursor-pointer text-center m-auto">'
                f'<span class="z-20 text-white font-bold text-lg">'
                f"+</span></div></div></a></td>"
            )

    def formatweek(self, theweek, y=""):
        s = ""
        round = f" rounded-{y}-lg" if y in ["t", "b"] else ""
        shadow = " shadow-lg dark:shadow dark:shadow-gray-700" if y == "b" else ""

        fd, ld = 0, 6

        if y == "t":
            days_list = [x[0] for x in theweek]
            fd = binary_search(days_list, 1)

        if y == "b":
            days_list = [x[0] for x in theweek]
            ld = days_list.index(self.lastday)

        for d, wd in theweek:
            x = "l" if wd == 0 else "r" if wd == len(theweek) - 1 else ""
            s += self.formatday(d, wd, y, x, fd, ld)

        return f'<tr class="divide-x divide-gray-200{shadow}{round} dark:divide-gray-600">{s}</tr>'
